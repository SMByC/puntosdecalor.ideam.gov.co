//  (c) Copyright SMByC-IDEAM, 2026
//  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>
//
//  Time window over the map: the track covers the whole period of the query
//  (left = "de", right = "a") and carries the same colour ramp used to paint
//  the hotspots, so it doubles as the legend. Inside it a window can be moved
//  and stretched from either edge; the hotspots it covers are highlighted on
//  the map and the rest are dimmed, so dragging it shows how the fires move
//  through time. The play button walks the window over the period on its own.

(function (window, document) {
    "use strict";

    var AF = window.AF = window.AF || {};

    var MINUTE = 60000;
    var HOUR = 60 * MINUTE;
    var DAY = 24 * HOUR;

    // below this many days each step of the window is one hour, otherwise one
    // day: the usual query is "yesterday and today", which as whole days would
    // give a slider with two positions
    var HOURLY_UP_TO_DAYS = 3;

    var PLAY_INTERVAL = 420;   // ms between two steps while playing
    var PLAY_FRAMES = 60;      // steps a full walk of the period takes

    var ICON_PLAY = 'M8 5.5v13l11-6.5z';
    var ICON_PAUSE = 'M8 5.5h3.4v13H8zM12.6 5.5H16v13h-3.4z';

    var PANEL_GAP = 6;     // px kept between the two date panels

    function clamp(value, low, high) {
        return value < low ? low : (value > high ? high : value);
    }

    function center_of(el) {
        var box = el.getBoundingClientRect();
        return box.left + box.width / 2;
    }

    function element(tag, className, parent) {
        var el = document.createElement(tag);
        if (className) {
            el.className = className;
        }
        if (parent) {
            parent.appendChild(el);
        }
        return el;
    }

    function format_date(milliseconds, with_time) {
        if (window.moment) {
            return window.moment(milliseconds).format(with_time ? 'YYYY-MM-DD HH:mm' : 'YYYY-MM-DD');
        }
        var iso = new Date(milliseconds).toISOString();
        return with_time ? iso.substr(0, 16).replace('T', ' ') : iso.substr(0, 10);
    }

    /* new AF.TimeSlider(container, {map: map, onchange: function (from_minutes,
       to_minutes, is_full) {...}})

       The callback receives the window as minute offsets from the start of the
       period -- the same units as the hotspot data -- and a flag telling that
       it covers everything, in which case nothing should be dimmed. */
    function TimeSlider(container, options) {
        options = options || {};
        this._onchange = options.onchange || function () {};
        this._map = options.map || null;

        this._t0 = 0;          // start of the period, in ms
        this._span = 0;        // length of the period, in minutes
        this._stepMs = DAY;
        this._steps = 1;       // number of steps of the whole period
        this._hourly = false;
        this._a = 0;           // window start, in steps
        this._b = 1;           // window end (exclusive), in steps
        this._playing = false;
        this._timer = null;

        this._build(container);
    }

    TimeSlider.prototype = {

        // -- construction --------------------------------------------------

        _build: function (container) {
            var self = this;

            var root = this._el = element('div', 'time-slider', container);
            root.hidden = true;
            root.setAttribute('aria-label', 'Línea de tiempo de los puntos de calor');

            // the date of each edge, floating over its grip
            this._popFrom = element('span', 'ts-pop ts-pop-from', root);
            this._popTo = element('span', 'ts-pop ts-pop-to', root);

            var row = element('div', 'ts-row', root);

            this._play = element('button', 'ts-btn ts-play', row);
            this._play.type = 'button';
            this._play.title = 'Recorrer el periodo';
            this._play.setAttribute('aria-label', 'Recorrer el periodo');
            this._play.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
                '<path d="' + ICON_PLAY + '" /></svg>';
            this._playIcon = this._play.querySelector('path');

            var track = this._track = element('div', 'ts-track', row);
            var ramp = element('div', 'ts-ramp', track);
            if (AF.rampGradient) {
                ramp.style.backgroundImage = AF.rampGradient('90deg');
            }
            this._maskLeft = element('div', 'ts-mask ts-mask-left', track);
            this._maskRight = element('div', 'ts-mask ts-mask-right', track);

            var win = this._win = element('div', 'ts-window', track);
            win.tabIndex = 0;
            win.setAttribute('aria-label', 'Mover el periodo resaltado');

            this._gripLeft = element('span', 'ts-grip ts-grip-left', win);
            this._gripRight = element('span', 'ts-grip ts-grip-right', win);
            [this._gripLeft, this._gripRight].forEach(function (grip, index) {
                grip.tabIndex = 0;
                grip.setAttribute('role', 'slider');
                grip.setAttribute('aria-label', index === 0
                    ? 'Inicio del periodo resaltado'
                    : 'Fin del periodo resaltado');
            });

            this._all = element('button', 'ts-btn ts-all', row);
            this._all.type = 'button';
            this._all.title = 'Ver todo el periodo';
            this._all.textContent = 'todo';

            // how many hotspots the window holds, under its middle
            this._popCount = element('span', 'ts-pop ts-pop-count', root);

            // the slider sits on top of the map: without this, dragging it
            // would pan the map and the wheel would zoom it
            if (window.L) {
                window.L.DomEvent.disableClickPropagation(root);
                window.L.DomEvent.disableScrollPropagation(root);
            }

            this._play.addEventListener('click', function () { self.togglePlay(); });
            this._all.addEventListener('click', function () { self.reset(); });

            this._dragHandler(win, 'move');
            this._dragHandler(this._gripLeft, 'left');
            this._dragHandler(this._gripRight, 'right');
            this._trackHandler(track);

            // the panels are placed from measurements, so they have to be laid
            // out again whenever the slider changes width
            if (window.ResizeObserver) {
                new window.ResizeObserver(function () { self._placePanels(); }).observe(root);
            } else {
                window.addEventListener('resize', function () { self._placePanels(); });
            }

            win.addEventListener('keydown', function (event) { self._onKey(event, 'move'); });
            this._gripLeft.addEventListener('keydown', function (event) { self._onKey(event, 'left'); });
            this._gripRight.addEventListener('keydown', function (event) { self._onKey(event, 'right'); });
        },

        // -- period --------------------------------------------------------

        /* Set the period of the current query: its start (ISO string or ms)
           and its length in minutes. A new period resets the window to cover
           everything, so nothing is dimmed until the user narrows it; the same
           period again (the region changed, the dates did not) keeps the window
           where the user left it. */
        setPeriod: function (start, span_minutes) {
            var t0 = (typeof start === 'string')
                ? (window.moment ? window.moment(start).valueOf() : Date.parse(start))
                : start;

            if (!start || !span_minutes || isNaN(t0)) {
                this.hide();
                return;
            }

            var same_period = (t0 === this._t0 && span_minutes === this._span);
            var was_from = this._a, was_to = this._b;

            this.stop();
            this._t0 = t0;
            this._span = span_minutes;
            this._hourly = (span_minutes * MINUTE) <= HOURLY_UP_TO_DAYS * DAY;
            this._stepMs = this._hourly ? HOUR : DAY;
            this._steps = Math.max(1, Math.ceil((span_minutes * MINUTE) / this._stepMs));
            this._a = same_period ? clamp(was_from, 0, this._steps - 1) : 0;
            this._b = same_period ? clamp(was_to, this._a + 1, this._steps) : this._steps;

            this._render();
            this._emit();
        },

        setCount: function (count) {
            this._popCount.innerHTML = '';
            var value = element('strong', null, this._popCount);
            value.textContent = (count || 0).toLocaleString('es-CO');
            this._popCount.appendChild(
                document.createTextNode(count === 1 ? ' punto de calor' : ' puntos de calor'));
            this._placePanels();
        },

        show: function () {
            this._el.hidden = false;
            document.body.classList.add('has-time-slider');
            this._placePanels();
        },

        hide: function () {
            this.stop();
            this._el.hidden = true;
            document.body.classList.remove('has-time-slider');
        },

        isFull: function () {
            return this._a === 0 && this._b === this._steps;
        },

        reset: function () {
            this.stop();
            this._set(0, this._steps);
        },

        // -- window --------------------------------------------------------

        _set: function (a, b) {
            a = clamp(Math.round(a), 0, this._steps - 1);
            b = clamp(Math.round(b), a + 1, this._steps);
            if (a === this._a && b === this._b) {
                return;
            }
            this._a = a;
            this._b = b;
            this._render();
            this._emit();
        },

        _emit: function () {
            var minutes = this._stepMs / MINUTE;
            this._onchange(this._a * minutes, this._b * minutes, this.isFull());
        },

        _render: function () {
            var left = (this._a * 100) / this._steps,
                right = (this._b * 100) / this._steps;

            this._win.style.left = left + '%';
            this._win.style.width = (right - left) + '%';
            this._maskLeft.style.width = left + '%';
            this._maskRight.style.width = (100 - right) + '%';

            this._el.classList.toggle('is-full', this.isFull());

            // the right grip sits on the end of the window, so the date it
            // stands for is the last step inside it, not the one after
            var value_now = this._stepLabel(this._a),
                value_end = this._stepLabel(Math.max(this._a, this._b - 1));

            this._popFrom.textContent = value_now;
            this._popTo.textContent = value_end;
            this._placePanels();

            // each grip stops at the other one, so that is the range to
            // announce: telling a screen reader about positions the widget
            // refuses to enter is worse than telling it nothing
            this._gripLeft.setAttribute('aria-valuemin', '0');
            this._gripLeft.setAttribute('aria-valuemax', String(this._b - 1));
            this._gripLeft.setAttribute('aria-valuenow', String(this._a));
            this._gripLeft.setAttribute('aria-valuetext', value_now);
            this._gripRight.setAttribute('aria-valuemin', String(this._a + 1));
            this._gripRight.setAttribute('aria-valuemax', String(this._steps));
            this._gripRight.setAttribute('aria-valuenow', String(this._b));
            this._gripRight.setAttribute('aria-valuetext', value_end);
        },

        /* Put the three panels where they belong: each date centred on its own
           grip and the count centred under the window. That is the rule; a
           panel only leaves the centre of its anchor for one of two reasons.
           Either the two dates would sit on top of each other, and then both
           are pushed apart by half the overlap each, or the pair reaches an
           edge of the slider, and then it slides back in as a block. The edge
           is the slider itself, panels are free to reach its border. They stay
           off the play and "todo" buttons by sitting in the strip of padding
           above and below the row rather than by keeping their distance. */
        _placePanels: function () {
            if (this._el.hidden) {
                return;
            }
            var root = this._el.getBoundingClientRect();
            if (!root.width) {
                return;
            }

            // "left" on an absolutely positioned child is measured from the
            // padding box of the slider, so the border has to be taken out of
            // the origin and put back into the bounds for a panel to be able
            // to sit flush against the edge of the slider
            var border = this._el.clientLeft,
                origin = root.left + border,
                min = -border,
                max = root.width - border;

            // the measured widths are fractional, so rounding them here would
            // be enough to push a panel back over the edge
            var left = center_of(this._gripLeft) - origin,
                right = center_of(this._gripRight) - origin,
                from_width = this._popFrom.getBoundingClientRect().width,
                to_width = this._popTo.getBoundingClientRect().width,
                count_width = this._popCount.getBoundingClientRect().width,
                from = left - from_width / 2,
                to = right - to_width / 2,
                overlap = (from + from_width + PANEL_GAP) - to;

            if (overlap > 0) {
                from -= overlap / 2;
                to += overlap / 2;
            }
            // the pair moves as a block, so pushing one back in pushes the other
            if (from < min) {
                to += min - from;
                from = min;
            }
            if (to + to_width > max) {
                to = max - to_width;
                from = Math.max(min, Math.min(from, to - from_width - PANEL_GAP));
            }

            this._popFrom.style.left = from.toFixed(1) + 'px';
            this._popTo.style.left = to.toFixed(1) + 'px';
            this._popCount.style.left = clamp(
                (left + right) / 2 - count_width / 2,
                min, Math.max(min, max - count_width)).toFixed(1) + 'px';
        },

        _stepLabel: function (step) {
            return format_date(this._t0 + step * this._stepMs, this._hourly);
        },

        // -- pointer -------------------------------------------------------

        _dragHandler: function (el, mode) {
            var self = this;

            el.addEventListener('pointerdown', function (event) {
                if (event.button !== undefined && event.button !== 0) {
                    return;
                }
                event.preventDefault();
                event.stopPropagation();
                self.stop();
                self._startDrag(el, event, mode);
            });
        },

        _startDrag: function (el, event, mode) {
            var self = this,
                rect = this._track.getBoundingClientRect(),
                start_x = event.clientX,
                a0 = this._a,
                b0 = this._b,
                width = b0 - a0;

            this._el.classList.add('is-dragging');
            try {
                el.setPointerCapture(event.pointerId);
            } catch (error) { /* capture is optional */ }

            function move(moveEvent) {
                var delta = ((moveEvent.clientX - start_x) / (rect.width || 1)) * self._steps;
                if (mode === 'move') {
                    var a = clamp(Math.round(a0 + delta), 0, self._steps - width);
                    self._set(a, a + width);
                } else if (mode === 'left') {
                    self._set(clamp(Math.round(a0 + delta), 0, b0 - 1), b0);
                } else {
                    self._set(a0, clamp(Math.round(b0 + delta), a0 + 1, self._steps));
                }
            }

            function up() {
                el.removeEventListener('pointermove', move);
                el.removeEventListener('pointerup', up);
                el.removeEventListener('pointercancel', up);
                self._el.classList.remove('is-dragging');
            }

            el.addEventListener('pointermove', move);
            el.addEventListener('pointerup', up);
            el.addEventListener('pointercancel', up);
        },

        // a press on the track moves the window there and keeps dragging it
        _trackHandler: function (track) {
            var self = this;

            track.addEventListener('pointerdown', function (event) {
                if (event.target !== track && event.target.parentNode !== track) {
                    return;
                }
                if (event.target === self._win || self._win.contains(event.target)) {
                    return;
                }
                if (event.button !== undefined && event.button !== 0) {
                    return;
                }
                event.preventDefault();
                event.stopPropagation();
                self.stop();

                var rect = track.getBoundingClientRect(),
                    at = ((event.clientX - rect.left) / (rect.width || 1)) * self._steps,
                    // a window covering the whole period cannot be moved: the
                    // first press on the track opens one instead
                    width = self.isFull()
                        ? Math.max(1, Math.round(self._steps / 12))
                        : self._b - self._a,
                    a = clamp(Math.round(at - width / 2), 0, self._steps - width);

                self._set(a, a + width);
                self._startDrag(self._win, event, 'move');
            });
        },

        // -- keyboard ------------------------------------------------------

        _onKey: function (event, mode) {
            var key = event.key,
                back = (key === 'ArrowLeft' || key === 'ArrowDown'),
                forward = (key === 'ArrowRight' || key === 'ArrowUp'),
                home = (key === 'Home'),
                end = (key === 'End');

            if (!back && !forward && !home && !end) {
                return;   // let Tab, Escape and the rest through
            }
            event.preventDefault();
            this.stop();

            var step = event.shiftKey ? Math.max(1, Math.round(this._steps / 10)) : 1,
                width = this._b - this._a,
                a = this._a,
                b = this._b;

            if (mode === 'move') {
                // moving keeps the width, so it is the position that is clamped
                a = home ? 0
                  : end ? this._steps - width
                  : clamp(a + (back ? -step : step), 0, this._steps - width);
                this._set(a, a + width);
            } else if (mode === 'left') {
                // an edge stops at the other one: without this clamp _set would
                // satisfy b >= a + 1 by pushing the right edge further right,
                // and holding the key would walk the whole window to the end
                a = home ? 0 : end ? b - 1 : a + (back ? -step : step);
                this._set(clamp(a, 0, b - 1), b);
            } else {
                b = home ? a + 1 : end ? this._steps : b + (back ? -step : step);
                this._set(a, clamp(b, a + 1, this._steps));
            }
        },

        // -- play ----------------------------------------------------------

        togglePlay: function () {
            if (this._playing) {
                this.stop();
            } else {
                this.play();
            }
        },

        play: function () {
            if (this._steps < 2) {
                return;
            }
            var self = this;

            // starting from the whole period there is nothing to watch: narrow
            // the window first so the walk is visible
            if (this.isFull()) {
                this._set(0, Math.max(1, Math.round(this._steps / 12)));
            }

            this._playing = true;
            this._play.classList.add('is-playing');
            this._play.title = 'Pausar';
            this._play.setAttribute('aria-label', 'Pausar');
            this._playIcon.setAttribute('d', ICON_PAUSE);

            // a long period would take minutes to walk one step at a time:
            // advance by a share of it so any period takes about the same
            var advance = Math.max(1, Math.round(this._steps / PLAY_FRAMES));
            // held from here on: letting the last step of a pass clip the
            // window against the end of the period would shorten it, and every
            // later pass would run with the shortened one
            var width = this._b - this._a;

            this._timer = window.setInterval(function () {
                var next = self._a + advance;
                if (next + width > self._steps) {
                    self._set(0, width);            // start over, same width
                } else {
                    self._set(next, next + width);
                }
            }, PLAY_INTERVAL);
        },

        stop: function () {
            if (this._timer) {
                window.clearInterval(this._timer);
                this._timer = null;
            }
            if (!this._playing) {
                return;
            }
            this._playing = false;
            this._play.classList.remove('is-playing');
            this._play.title = 'Recorrer el periodo';
            this._play.setAttribute('aria-label', 'Recorrer el periodo');
            this._playIcon.setAttribute('d', ICON_PLAY);
        }
    };

    AF.TimeSlider = TimeSlider;

}(window, document));
