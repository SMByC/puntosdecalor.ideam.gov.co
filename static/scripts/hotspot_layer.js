//  (c) Copyright SMByC-IDEAM, 2026
//  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>
//
//  Hotspots drawn on a <canvas> and coloured by date.
//
//  Why not markers: one DOM node (and one Leaflet layer object) per hotspot
//  does not scale to the hundreds of thousands of points a long period over
//  the whole country returns, which is why the page used to cluster them.
//  Clustering hides *when* each point was detected, so it is replaced here by
//  a single canvas: the points are projected once into typed arrays and every
//  redraw is plain arithmetic over those arrays.
//
//  The points arrive ordered by date, so highlighting a period is a slice of
//  the arrays -- no search, no per-point state. Two canvases are stacked: the
//  lower one holds every point (dimmed while a time window is active) and is
//  redrawn only when the map moves; the upper one holds just the window and is
//  the only thing redrawn while the time slider is being dragged.

(function (window, L) {
    "use strict";

    var AF = window.AF = window.AF || {};

    // COLOUR RAMP ----------------------------------------------------------
    //
    // Old -> new, built around the red of the page (#CC3D36, H 3 / S 74 / B 80),
    // which is the sixth stop itself. The hue turns from yellow down to that
    // red, the saturation climbs from pale to the brand's, and the brightness
    // falls, so lightness decreases steadily with age (L* 93 down to 40) and the
    // most recent detections are the ones that stand out over the light basemap
    // (CartoDB light_all). The whole ramp keeps to the warm half of the wheel,
    // away from the purple of the burned area layer, and the dark outline of
    // every point is what keeps the pale end readable.

    var RAMP_STOPS = [
        '#FFEAA3',   // oldest, pale yellow  H 46  S 36  B 100
        '#FCCF81',   //                      H 38  S 49  B  99
        '#F7A863',   //                      H 28  S 60  B  97
        '#ED7A4C',   //                      H 17  S 68  B  93
        '#DF543E',   //                      H  8  S 72  B  88
        '#CC3D36',   // the red of the page  H  3  S 74  B  80
        '#B2252D'    // newest, dark red     H 357 S 79  B  70
    ];

    // the ramp is sampled into this many colours: a point is drawn from a
    // pre-rendered sprite, so a continuous ramp would mean a sprite per point
    var RAMP_STEPS = 64;

    // the oldest points are drawn slightly smaller than the newest ones, so
    // age reads even where the colours are close
    var RADIUS_MIN_FACTOR = 0.78;
    var RADIUS_MAX_FACTOR = 1.12;

    var TAU = Math.PI * 2;

    function hex_to_rgb(hex) {
        return [
            parseInt(hex.substr(1, 2), 16),
            parseInt(hex.substr(3, 2), 16),
            parseInt(hex.substr(5, 2), 16)
        ];
    }

    var RAMP_RGB = [];
    for (var s = 0; s < RAMP_STOPS.length; s++) {
        RAMP_RGB.push(hex_to_rgb(RAMP_STOPS[s]));
    }

    // colour of an age t, 0 = oldest ... 1 = newest
    function ramp_color(t) {
        t = t < 0 ? 0 : (t > 1 ? 1 : t);
        var pos = t * (RAMP_RGB.length - 1),
            i = Math.min(Math.floor(pos), RAMP_RGB.length - 2),
            f = pos - i,
            a = RAMP_RGB[i],
            b = RAMP_RGB[i + 1];
        return 'rgb(' + Math.round(a[0] + (b[0] - a[0]) * f) + ',' +
                        Math.round(a[1] + (b[1] - a[1]) * f) + ',' +
                        Math.round(a[2] + (b[2] - a[2]) * f) + ')';
    }

    // the same ramp as a CSS gradient, so the legend of the time slider and
    // the points on the map cannot drift apart
    function ramp_gradient(direction) {
        var parts = [], i;
        for (i = 0; i < RAMP_STOPS.length; i++) {
            parts.push(RAMP_STOPS[i] + ' ' +
                       Math.round((i * 100) / (RAMP_STOPS.length - 1)) + '%');
        }
        return 'linear-gradient(' + (direction || '90deg') + ', ' + parts.join(', ') + ')';
    }

    AF.rampColor = ramp_color;
    AF.rampGradient = ramp_gradient;

    // SPRITES --------------------------------------------------------------
    // Drawing a point is then a single drawImage() instead of building and
    // filling a path, and the outline that keeps the pale colours readable
    // over the basemap is painted once per colour instead of once per point.

    var DOT_STROKE = 'rgba(60, 20, 15, 0.55)';

    // The zoom range gives a dozen radii at most and the map keeps coming back
    // to them, so a set is built once and then reused.
    var sprite_cache = {};

    function sprites_for(radius, dpr) {
        var key = radius + 'x' + dpr;
        if (!sprite_cache[key]) {
            sprite_cache[key] = build_sprites(radius, dpr);
        }
        return sprite_cache[key];
    }

    // One set of sprites for the whole layer: a point of the time window has to
    // look exactly like the same point does when the window covers everything,
    // so the only thing that separates them is the opacity of the points around
    // them. The dark outline keeps the pale colours readable over the basemap.
    function build_sprites(radius, dpr) {
        var box = Math.ceil((radius * RADIUS_MAX_FACTOR + 1.6) * 2),
            center = box / 2,
            sprites = new Array(RAMP_STEPS),
            i, t, r, canvas, ctx;

        for (i = 0; i < RAMP_STEPS; i++) {
            t = i / (RAMP_STEPS - 1);
            r = radius * (RADIUS_MIN_FACTOR + (RADIUS_MAX_FACTOR - RADIUS_MIN_FACTOR) * t);

            canvas = document.createElement('canvas');
            canvas.width = canvas.height = Math.max(1, Math.round(box * dpr));
            ctx = canvas.getContext('2d');
            ctx.scale(dpr, dpr);

            ctx.beginPath();
            ctx.arc(center, center, r, 0, TAU);
            ctx.fillStyle = ramp_color(t);
            ctx.fill();
            ctx.strokeStyle = DOT_STROKE;
            ctx.lineWidth = 0.9;
            ctx.stroke();

            sprites[i] = canvas;
        }

        // the points are drawn in device pixels, with the canvas transform
        // left at identity: the three argument drawImage() with whole
        // coordinates is by far the fastest path, and at this size the
        // rounding is under one device pixel
        sprites.box = Math.max(1, Math.round(box * dpr));
        return sprites;
    }

    // LAYER ----------------------------------------------------------------

    // the points are projected once at this zoom and only multiplied by a
    // scale factor afterwards, so panning and zooming never reprojects
    var REF_ZOOM = 20;

    // how much of the original opacity the points outside the window keep
    var DIM_ALPHA = 0.22;

    var HotspotLayer = L.Renderer.extend({

        options: {
            padding: 0.12,
            pane: 'afHotspotPane'
        },

        initialize: function (options) {
            L.Renderer.prototype.initialize.call(this, options);
            this._clearData();
        },

        // -- lifecycle -----------------------------------------------------

        onAdd: function (map) {
            if (!map.getPane(this.options.pane)) {
                var pane = map.createPane(this.options.pane);
                // over the region outline and the burned area polygons,
                // under the popups
                pane.style.zIndex = 450;
                // the canvas is only a picture: every interaction (dragging
                // the map, clicking a point) is handled through map events
                pane.style.pointerEvents = 'none';
            }
            // Renderer.onAdd ends in _update(), which draws
            L.Renderer.prototype.onAdd.call(this, map);
        },

        // A zoom fires moveend and then viewreset, and both end in _update:
        // without this the whole layer would be painted twice per zoom step.
        // The flag makes _update do the geometry only and leaves the drawing
        // to _reset, which runs last.
        getEvents: function () {
            var events = L.Renderer.prototype.getEvents.call(this);
            events.viewprereset = this._onViewPreReset;
            return events;
        },

        _onViewPreReset: function () {
            this._postponeDraw = true;
        },

        _reset: function () {
            L.Renderer.prototype._reset.call(this);
            if (this._postponeDraw) {
                this._postponeDraw = false;
                this._draw();
            }
        },

        _initContainer: function () {
            var container = this._container = L.DomUtil.create('div', 'leaflet-layer af-hotspots');
            this._base = document.createElement('canvas');
            this._window = document.createElement('canvas');
            container.appendChild(this._base);
            container.appendChild(this._window);
            this._baseCtx = this._base.getContext('2d');
            this._windowCtx = this._window.getContext('2d');
        },

        _destroyContainer: function () {
            L.DomUtil.remove(this._container);
            delete this._baseCtx;
            delete this._windowCtx;
            delete this._base;
            delete this._window;
            delete this._container;
        },

        // -- data ----------------------------------------------------------

        _clearData: function () {
            this._n = 0;
            this._x = null;          // projected at REF_ZOOM
            this._y = null;
            this._minutes = null;    // minutes since the start of the period
            this._ids = null;
            this._colors = null;     // index into the ramp
            this._hasWindow = false;
            this._w0 = 0;
            this._w1 = 0;
            this._span = 1;
        },

        /* Load the payload of active_fires.json. */
        setData: function (data) {
            var n = (data && data.n) | 0;

            this._clearData();
            this._n = n;
            this._span = Math.max(1, (data && data.span) || 1);

            if (n) {
                var crs = (this._map && this._map.options.crs) || L.CRS.EPSG3857,
                    lon = data.lon, lat = data.lat, m = data.m, ids = data.id,
                    last = this._span - 1 || 1,
                    steps = RAMP_STEPS - 1,
                    previous = 0, point, i;

                this._x = new Float64Array(n);
                this._y = new Float64Array(n);
                this._minutes = new Int32Array(n);
                this._ids = new Int32Array(n);
                this._colors = new Uint8Array(n);

                for (i = 0; i < n; i++) {
                    point = crs.latLngToPoint(L.latLng(lat[i], lon[i]), REF_ZOOM);
                    this._x[i] = point.x;
                    this._y[i] = point.y;
                    this._minutes[i] = m[i];
                    previous += ids[i];
                    this._ids[i] = previous;
                    this._colors[i] = Math.max(0, Math.min(steps,
                        Math.round((m[i] / last) * steps)));
                }
            }

            this._draw();
            return this;
        },

        clearData: function () {
            this._clearData();
            this._draw();
            return this;
        },

        count: function () {
            return this._n;
        },

        /* Position of the point number `index`, back from the projected
           coordinates it is drawn from. */
        latLngAt: function (index) {
            if (!this._n || index < 0 || index >= this._n) {
                return null;
            }
            var crs = (this._map && this._map.options.crs) || L.CRS.EPSG3857;
            return crs.pointToLatLng(L.point(this._x[index], this._y[index]), REF_ZOOM);
        },

        // -- time window ---------------------------------------------------

        /* Highlight [from_minutes, to_minutes) and dim everything else. The
           points are ordered by date, so the window is a slice. */
        setTimeWindow: function (from_minutes, to_minutes) {
            var was_dimmed = this._hasWindow;
            this._w0 = this._lowerBound(from_minutes);
            this._w1 = this._lowerBound(to_minutes);
            this._hasWindow = true;
            if (!was_dimmed) {
                this._drawBase();
            }
            this._drawWindow();
            return this;
        },

        clearTimeWindow: function () {
            if (!this._hasWindow) {
                return this;
            }
            this._hasWindow = false;
            this._w0 = this._w1 = 0;
            this._drawBase();
            this._drawWindow();
            return this;
        },

        windowCount: function () {
            return this._hasWindow ? this._w1 - this._w0 : this._n;
        },

        // first index whose minute offset is >= value
        _lowerBound: function (value) {
            var low = 0, high = this._n, mid;
            while (low < high) {
                mid = (low + high) >> 1;
                if (this._minutes[mid] < value) {
                    low = mid + 1;
                } else {
                    high = mid;
                }
            }
            return low;
        },

        // -- hit testing ---------------------------------------------------

        /* The nearest hotspot to a position, or null. Points of the active
           window are drawn on top, so they win the click. */
        hitTest: function (latlng, tolerance) {
            if (!this._n || !this._map) {
                return null;
            }
            var point = this._map.latLngToLayerPoint(latlng),
                limit = tolerance || (L.Browser.touch ? 14 : 9),
                found = -1;

            if (this._hasWindow && this._w1 > this._w0) {
                found = this._nearest(this._w0, this._w1, point, limit);
            }
            if (found < 0) {
                found = this._nearest(0, this._n, point, limit);
            }
            if (found < 0) {
                return null;
            }

            return {
                id: this._ids[found],
                minutes: this._minutes[found],
                latlng: this.latLngAt(found)
            };
        },

        _nearest: function (from, to, point, limit) {
            var scale = this._scale, origin = this._origin,
                best = -1, best_distance = limit * limit,
                x = this._x, y = this._y,
                i, dx, dy, distance;

            if (!origin) {
                return -1;
            }
            for (i = from; i < to; i++) {
                dx = x[i] * scale - origin.x - point.x;
                if (dx > limit || dx < -limit) {
                    continue;
                }
                dy = y[i] * scale - origin.y - point.y;
                if (dy > limit || dy < -limit) {
                    continue;
                }
                distance = dx * dx + dy * dy;
                if (distance <= best_distance) {
                    // on a tie the newest point wins, it is the one on top
                    best_distance = distance;
                    best = i;
                }
            }
            return best;
        },

        // -- drawing -------------------------------------------------------

        // small enough not to fill the map at country level, big enough to be
        // tapped when zoomed in
        _radiusForZoom: function (zoom) {
            var radius = 2 + (zoom - 5) * 0.42;
            if (L.Browser.touch) {
                radius += 0.5;
            }
            return Math.max(1.8, Math.min(8, radius));
        },

        _update: function () {
            if (this._map._animatingZoom && this._bounds) {
                return;
            }
            L.Renderer.prototype._update.call(this);

            var bounds = this._bounds,
                size = bounds.getSize(),
                dpr = Math.min(window.devicePixelRatio || 1, 2),
                radius = this._radiusForZoom(this._zoom),
                width = Math.round(size.x * dpr),
                height = Math.round(size.y * dpr),
                canvases = [this._base, this._window],
                canvas, i;

            L.DomUtil.setPosition(this._container, bounds.min);
            this._container.style.width = size.x + 'px';
            this._container.style.height = size.y + 'px';

            for (i = 0; i < canvases.length; i++) {
                canvas = canvases[i];
                // assigning the size reallocates the canvas, so only do it
                // when it really changed (panning does not change it)
                if (canvas.width !== width || canvas.height !== height) {
                    canvas.width = width;
                    canvas.height = height;
                    canvas.style.width = size.x + 'px';
                    canvas.style.height = size.y + 'px';
                }
            }

            if (radius !== this._radius || dpr !== this._dpr) {
                this._radius = radius;
                this._dpr = dpr;
                this._sprites = sprites_for(radius, dpr);
            }

            // the points are kept in layer coordinates: only the scale and the
            // origin of the map change, never the projected values. Fold the
            // scale, the origin, the corner of the canvas and the device pixel
            // ratio into one multiply and one add per point.
            this._scale = this._map.getZoomScale(this._zoom, REF_ZOOM);
            this._origin = this._map.getPixelOrigin();
            this._pixelScale = this._scale * dpr;
            this._offsetX = -(this._origin.x + bounds.min.x) * dpr;
            this._offsetY = -(this._origin.y + bounds.min.y) * dpr;

            if (!this._postponeDraw) {
                this._draw();
            }
        },

        _draw: function () {
            this._drawBase();
            this._drawWindow();
        },

        _prepare: function (ctx) {
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        },

        _drawBase: function () {
            if (!this._baseCtx || !this._bounds) {
                return;
            }
            var ctx = this._baseCtx;
            this._prepare(ctx);
            if (!this._n) {
                return;
            }
            ctx.globalAlpha = this._hasWindow ? DIM_ALPHA : 1;
            this._paint(ctx, 0, this._n, this._sprites);
            ctx.globalAlpha = 1;
        },

        _drawWindow: function () {
            if (!this._windowCtx || !this._bounds) {
                return;
            }
            var ctx = this._windowCtx;
            this._prepare(ctx);
            if (!this._n || !this._hasWindow) {
                return;
            }
            this._paint(ctx, this._w0, this._w1, this._sprites);
        },

        /* The hot loop: one multiply-add, two comparisons and one blit per
           point, all in device pixels with the canvas transform at identity.
           Points are drawn oldest first, so the newest ones end up on top. */
        _paint: function (ctx, from, to, sprites) {
            var scale = this._pixelScale,
                offset_x = this._offsetX,
                offset_y = this._offsetY,
                half = sprites.box / 2,
                width = ctx.canvas.width + half,
                height = ctx.canvas.height + half,
                x = this._x, y = this._y, colors = this._colors,
                i, px, py;

            for (i = from; i < to; i++) {
                px = x[i] * scale + offset_x;
                if (px < -half || px > width) {
                    continue;
                }
                py = y[i] * scale + offset_y;
                if (py < -half || py > height) {
                    continue;
                }
                ctx.drawImage(sprites[colors[i]], (px - half) | 0, (py - half) | 0);
            }
        }
    });

    AF.HotspotLayer = HotspotLayer;
    AF.hotspotLayer = function (options) {
        return new HotspotLayer(options);
    };

}(window, window.L));
