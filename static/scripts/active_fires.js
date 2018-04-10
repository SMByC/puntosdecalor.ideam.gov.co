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

//==============================================================================
//run when DOM is ready

jQuery(document).ready(function($){

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

});
