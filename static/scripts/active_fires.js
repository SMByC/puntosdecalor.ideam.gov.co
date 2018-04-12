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

//==============================================================================
//run when DOM is ready

$(function () {
    // wait cursor for request ajax
    var map_mouse;
    $(document).ajaxStart(function() {
        $(document.body).css({'cursor' : 'wait'});
        map_mouse = $('#active_fires_map').css('cursor');
        $('#active_fires_map').css({'cursor' : 'wait'});
        $('.month-wrapper table .day').css({'cursor' : 'wait'});
        $('.custom-shortcut a').css({'cursor' : 'wait'});
    }).ajaxStop(function() {
        $(document.body).css({'cursor' : 'default'});
        $('#active_fires_map').css({'cursor' : map_mouse});
        $('.month-wrapper table .day').css({'cursor' : 'pointer'});
        $('.custom-shortcut a').css({'cursor' : 'pointer'});
    });

    //MENU-HEADER
    //activacion del submenu del menu principal de navegacion
    var sublink_activated = false;
    $("div#header-menu").find("li").each(function() {
        if ( (typeof $(this).find("a").attr('href') != 'undefined') && ($(this).find("a").attr('href').replace('/','') == window.location.href.split("/").reverse()[1]) ) {
            $(this).addClass("menuOn");
            sublink_activated = true;
        } else {
            $(this).removeClass("menuOn")
        }
    });
    if (sublink_activated == false) {
        $("div#header-menu").find("li").first().addClass("menuOn")
    }

    // set the class to select2
    $('#region').select2({
        language: "es"
    });
});
