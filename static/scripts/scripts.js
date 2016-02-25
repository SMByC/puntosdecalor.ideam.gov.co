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
    $('ul#levelOne').mouseover(function() {
        $(this).find("li.menuOn").addClass("menuOff").removeClass("menuOn");
    }).mouseout(function() {
        $(this).find("li.menuOff").addClass("menuOn").removeClass("menuOff");
    });

    //desaparecer el submenu cuando se pasa por el titulo
    $('#header-title  #title').mouseover(function() {
        $('ul#levelOne').find("li.menuOn").addClass("menuOff").removeClass("menuOn");
    }).mouseout(function() {
        $('ul#levelOne').find("li.menuOff").addClass("menuOn").removeClass("menuOff");
    }).click(function() {
        $('ul#levelOne').find("li.menuOff").removeClass("menuOff");
    });

    //CONTENT
    //activar/desactivar mas informacion en el titulo del contenido
    var moreInfoBlock = $("#title-content #more-info");
    var toggleInfo = function(){
        if (moreInfoBlock.html() == "(-)"){
            moreInfoBlock
                .html("(+)")
                .attr("title","más información")
        } else {
            moreInfoBlock
                .html("(-)")
                .attr("title","esconder información")
        }
        $("#title-content #more-info-text").slideToggle();
    };

    moreInfoBlock.click(function () {
        toggleInfo();
    });


    //ACTIVACIONES
    //activar o expandir la informacion de la pagina (more-info) por defecto
    //solo si hay texto
    if ( $.trim($("#more-info-text").text()).length != 0 ) {
        toggleInfo();
    }

    //run when everything on the page as loaded.
    $(window).load(function(){
    //loader gif and content activation
        FirstLoadActivationMenus();

    });

});