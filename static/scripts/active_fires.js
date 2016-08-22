//FUCTIONS----------------------------------------------------------


//==============================================================================
//run when DOM is ready

jQuery(document).ready(function($){

    var mantenimiento = false;
    if (mantenimiento) {
        $("#warning-message").show();
    }
    //MENU-HEADER
    //activacion del submenu del menu principal de navegacion
    var sublink_activated = false;
    $("div#header-menu").find("li").each(function() {
        if ($(this).find("a").attr('href').replace('/','') == window.location.href.split("/").reverse()[1]) {
            $(this).addClass("menuOn");
            sublink_activated = true;
        } else {
            $(this).removeClass("menuOn")
        }
    });
    if (sublink_activated == false) {
        $("div#header-menu").find("li").first().addClass("menuOn")
    }

    //run when everything on the page as loaded.
    $(window).load(function(){
    //loader gif and content activation

    });

});
