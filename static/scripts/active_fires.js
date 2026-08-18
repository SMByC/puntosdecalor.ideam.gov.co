//  (c) Copyright IDEAM-2018
//  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

//FUCTIONS----------------------------------------------------------

// function for change get parameters
function updateQueryStringParameter(uri, key, value) {
    // use value=undefined for delete parameter
    var i = uri.indexOf('#');
    var hash = i === -1 ? '' : uri.substr(i);
    uri = i === -1 ? uri : uri.substr(0, i);

    var re = new RegExp("([?&])" + key + "=.*?(&|$)", "i");
    var separator = uri.indexOf('?') !== -1 ? "&" : "?";

    if (!value) {
        // remove key-value pair if value is empty
        uri = uri.replace(new RegExp("([?&]?)" + key + "=[^&]*", "i"), '');
        if (uri.slice(-1) === '?') {
            uri = uri.slice(0, -1);
        }
        // replace first occurrence of & by ? if no ? is present
        if (uri.indexOf('?') === -1) uri = uri.replace(/&/, '?');
    } else if (uri.match(re)) {
        uri = uri.replace(re, '$1' + key + "=" + value + '$2');
    } else {
        uri = uri + separator + key + "=" + value;
    }
    return uri + hash;
}

function updateUrlParameter(key, value) {
    window.history.pushState('', '', updateQueryStringParameter(window.location.search, key, value));
}

function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

//RESPONSIVE HELPERS------------------------------------------------
// the layout has two targets: phones (lateral panel as a drawer) and
// laptop/desktop (lateral panel docked beside the map)

var AF_DESKTOP_LAYOUT = "(min-width: 900px)";

function media_matches(query) {
    return window.matchMedia && window.matchMedia(query).matches;
}

// the lateral panel is docked (not a drawer) on laptop/desktop
function is_desktop_layout() {
    return media_matches(AF_DESKTOP_LAYOUT);
}

// keep the fitted region away from the map controls/edges
function map_fit_padding() {
    return is_desktop_layout() ? [24, 24] : [12, 12];
}

//==============================================================================
//run when DOM is ready

$(function () {

    //LOADING FEEDBACK
    // a small indicator over the map while the data is being requested
    $(document).ajaxStart(function () {
        $('#map-loading').prop('hidden', false);
        $(document.body).css({'cursor': 'wait'});
        // a class, not an inline cursor: reading the computed cursor here and
        // writing it back on ajaxStop pinned whatever leaflet (or the hotspot
        // hover) happened to have set, and the map kept it for good -- which
        // also killed the grabbing cursor while dragging
        $('#active_fires_map').addClass('af-busy');
        $('.month-wrapper table .day').css({'cursor': 'wait'});
        $('.custom-shortcut a').css({'cursor': 'wait'});
    }).ajaxStop(function () {
        $('#map-loading').prop('hidden', true);
        $(document.body).css({'cursor': 'default'});
        $('#active_fires_map').removeClass('af-busy');
        $('.month-wrapper table .day').css({'cursor': 'pointer'});
        $('.custom-shortcut a').css({'cursor': 'pointer'});
    });

    //LATERAL PANEL (drawer on mobile, docked panel on desktop)
    var $body = $('body');
    var $panel_toggle = $('#panel-toggle');

    function open_panel() {
        $body.addClass('panel-open');
        $panel_toggle.attr('aria-expanded', 'true');
        // move the focus into the panel for keyboard/screen reader users
        window.setTimeout(function () { $('#panel-close').trigger('focus'); }, 60);
    }

    function close_panel() {
        if (!$body.hasClass('panel-open')) return;
        $body.removeClass('panel-open');
        $panel_toggle.attr('aria-expanded', 'false').trigger('focus');
    }

    function toggle_panel() {
        if ($body.hasClass('panel-open')) close_panel();
        else open_panel();
    }

    $panel_toggle.on('click', toggle_panel);
    $('#panel-close').on('click', close_panel);
    $('#panel-backdrop').on('click', close_panel);

    // on the docked layout the panel is always visible: reset the drawer state
    if (window.matchMedia) {
        var desktop_mq = window.matchMedia(AF_DESKTOP_LAYOUT);
        var on_layout_change = function (event) {
            if (event.matches) {
                $body.removeClass('panel-open');
                $panel_toggle.attr('aria-expanded', 'false');
            }
        };
        if (desktop_mq.addEventListener) desktop_mq.addEventListener('change', on_layout_change);
        else if (desktop_mq.addListener) desktop_mq.addListener(on_layout_change);
    }

    //MODAL WINDOWS (contexto / acerca de)
    function open_modal(id) {
        var modal = document.getElementById(id);
        if (!modal) return;
        if (typeof modal.showModal === 'function') {
            if (!modal.open) modal.showModal();
        } else {
            // fallback for browsers without <dialog> support
            modal.setAttribute('open', '');
            modal.classList.add('is-open');
        }
    }

    function close_modal(modal) {
        if (!modal) return;
        if (typeof modal.close === 'function' && modal.open && !modal.classList.contains('is-open')) {
            modal.close();
        } else {
            modal.removeAttribute('open');
            modal.classList.remove('is-open');
        }
    }

    // any element with data-modal-open="<id>" opens its modal
    $(document).on('click', '[data-modal-open]', function (event) {
        event.preventDefault();
        open_modal($(this).data('modal-open'));
    });

    // close buttons
    $(document).on('click', '[data-modal-close]', function () {
        close_modal($(this).closest('dialog')[0]);
    });

    // when the user clicks outside of the modal content, close it
    $('dialog.modal').on('click', function (event) {
        if (event.target === this) close_modal(this);
    });

    //KEYBOARD
    // Escape closes the drawer, but only when it is the outermost thing open:
    // a drop-list, the date picker or a modal must be closed first
    function something_is_open_over_the_panel() {
        return $('.select2-container--open').length > 0 ||
               $('.date-picker-wrapper:visible').length > 0 ||
               $('dialog.modal[open]').length > 0;
    }

    $(document).on('keydown', function (event) {
        if (event.key !== 'Escape' && event.keyCode !== 27) return;
        if (event.isDefaultPrevented() || something_is_open_over_the_panel()) return;
        // <dialog> closes itself with Escape, only the drawer needs help
        close_panel();
    });

    //DROP-LISTS (select2)
    // The list is attached to the panel instead of to <body>: select2 places it
    // once, in page coordinates, and the panel is a drawer that slides in and
    // out. Attached to the body the list stays where the control *was* when it
    // opened (misplaced if it is opened while the drawer is still sliding) and
    // it survives on screen after the drawer is closed. As a child of the panel
    // it travels with it.
    var $panel = $('#lateral-content');

    $('#region').select2({
        language: "es",
        width: '100%',
        dropdownAutoWidth: false,
        dropdownParent: $panel
    });

    $('#burned_area').select2({
        language: "es",
        width: '100%',
        dropdownAutoWidth: false,
        // keep the list open to pick several months in a row
        closeOnSelect: false,
        placeholder: $('#burned_area').data('placeholder') || '',
        templateSelection: function (data, container) {
            var text = data.text || '';
            if (/^\d{4}$/.test(text)) {
                $(container).addClass('burned-area-year-shortcut-choice');
            }
            return text;
        },
        dropdownParent: $panel
    });

    // removing a choice with its x focuses the search field, and select2 4.1
    // answers that focus by opening the drop-list; swallow that one opening.
    // Removals from the open list are unaffected: the list is already open,
    // so no "opening" event follows and the flag is reset on close
    var skip_open_after_unselect = false;
    $('#burned_area').on('select2:unselecting', function () {
        skip_open_after_unselect = true;
    });
    $('#burned_area').on('select2:opening', function (event) {
        if (!skip_open_after_unselect) return;
        skip_open_after_unselect = false;
        event.preventDefault();
    });
    $('#burned_area').on('select2:close', function () {
        skip_open_after_unselect = false;
    });

    // a drop-list left open would be hidden with the drawer and reopen with it
    $('#panel-close, #panel-backdrop').on('click', function () {
        $('#region, #burned_area').select2('close');
    });

});
