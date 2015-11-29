//FUCTIONS----------------------------------------------------------

//funcion que asigna el ancho(y de la pagina) segun el ancho del 
//menu de activacion (para expandir la pagina si es necesario)
var setWidthMenuActivation = function(){
    var MenuActivationWidth = 0;

    is_menu_0 = false;
    
    $('#menu-0 .button').each(function() {
        MenuActivationWidth += $(this).width()+parseInt($(this).css("padding-left"), 10)+parseInt($(this).css("padding-right"), 10);
        is_menu_0 = true;
    });

    is_menu_1 = false;

    $('#menu-1 .button').each(function() {
        MenuActivationWidth += $(this).width()+parseInt($(this).css("padding-left"), 10)+parseInt($(this).css("padding-right"), 10);
        is_menu_1 = true;
    });

    is_menu_2 = false;
        
    $('#menu-2 .button').each(function() {
        MenuActivationWidth += $(this).width()+parseInt($(this).css("padding-left"), 10)+parseInt($(this).css("padding-right"), 10);
        is_menu_2 = true;
    });

    is_menu_0_loop = false;

    $('#menu-0 .buttonloop').each(function() {
        MenuActivationWidth += $(this).width()+parseInt($(this).css("padding-left"), 10)+parseInt($(this).css("padding-right"), 10);
        is_menu_0_loop = true;
    });

    is_menu_1_loop = false;

    $('#menu-1 .buttonloop').each(function() {
        MenuActivationWidth += $(this).width()+parseInt($(this).css("padding-left"), 10)+parseInt($(this).css("padding-right"), 10);
        is_menu_1_loop = true;
    });

    is_menu_2_loop = false;

    $('#menu-2 .buttonloop').each(function() {
        MenuActivationWidth += $(this).width()+parseInt($(this).css("padding-left"), 10)+parseInt($(this).css("padding-right"), 10);
        is_menu_2_loop = true;
    });

    MenuActivationWidth += 70 + 32*(is_menu_0+is_menu_1+is_menu_2+is_menu_0_loop+is_menu_1_loop+is_menu_2_loop);

    //alert(MenuActivationWidth)
    //$('#wrap-content').css("width",MenuActivationWidth); //lo hace el setWidthImageScrollMulti
    $('#wrapper').css("min-width",MenuActivationWidth+15);
    return MenuActivationWidth;
};
//TODO:

// funcion que cambia el ancho del bloque de contenido segun el tamaño de
// imagenes o tablas activadas/visibles
jQuery.fn.exists = function(){return jQuery(this).length>0;};
var setWidthImageScrollMulti = function(){
    //primero asignar tamaño segun los tabs de activacion
    tabsWidth=setWidthMenuActivation();

    var extraSpace = 4;
    var imgsWidth = 0;
    var scrollNumber = 1;
    var imgPadding = parseInt($('.image').css('padding-left'),10) +
                     parseInt($('.image').css('padding-right'),10) +
                     2*parseInt($('.image').css('border-left-width'),10);
    var windowWidth=parseInt($('#main').css('width'),10);
    //busca todos los elementos activados para capturar su anchura,imagnenes y tablas
    while ( $('#image-scroll-'+scrollNumber).exists() ) {
        var tempWidth = 0;
        var isTable = false;
        //para tablas
        $('#image-scroll-'+scrollNumber+' .image table').each(function() {
            if (!$(this).parent().hasClass('off-1') && 
                !$(this).parent().hasClass('off-2')){
                tempWidth += $(this).width() + imgPadding + 2 + extraSpace;
                //alert(scrollNumber+"sss"+tempWidth+"aaa"+this.width);
                isTable = true
            }
        });
        //para imagenes
        $('#image-scroll-'+scrollNumber+' .image img').each(function() {
            if (!$(this).parent().hasClass('off-1') && 
                !$(this).parent().hasClass('off-2') && !isTable){
                tempWidth += $(this).width() + imgPadding + extraSpace;
                //alert(scrollNumber+"sss"+tempWidth+"aaa"+this.width);
            }
        });
        if (tempWidth>imgsWidth){
            imgsWidth = tempWidth;
        }
        
        if (imgsWidth > windowWidth-12){
            $('#wrap-content').css("width",windowWidth-12);
        } else if ( tabsWidth > imgsWidth ){
            $('#wrap-content').css("width",tabsWidth);
        } else {
            $('#wrap-content').css("width",imgsWidth+2*parseInt($('#content').css('padding-right'),10));
        }
        
        $('#image-scroll-'+scrollNumber).css("width",imgsWidth);
        //      $("#dev").html("valor:"+imgsWidth+"aaa"+$('#main').css('width'));
        scrollNumber++;
    }
};

//TODO:

var IsImageOk = function(img) {
    // During the onload event, IE correctly identifies any images that
    // werenâ€™t downloaded as not complete. Others should too. Gecko-based
    // browsers act like NS4 in that they report this incorrectly.
    if (!img.complete) {
        return false;
    }
    
    // However, they do have two very useful properties: naturalWidth and
    // naturalHeight. These give the true size of the image. If it failed
    // to load, either of these should be zero.

    if (typeof img.naturalWidth != "undefined" && img.naturalWidth == 0) {
        return false;
    }
    // No other way of checking: assume itâ€™s ok.
    return true;
};

var loadImage = function(img,button) {
    $(img).parent().hide();
    if (IsImageOk(img)) {
        $(img).attr('src', $(img).attr('_src'));
        $(img).parent().fadeIn(500);
        // TODO: animated gif in IE
        setWidthImageScrollMulti();
    } else {
        $('#main').css('cursor', 'wait');
        $(button).css('cursor', 'wait');
        $(button).addClass('loading');
        $(img).attr('src', $(img).attr('_src'));
        $(img).load(function() {
            $(this).parent().fadeIn(500);
            // TODO: animated gif in IE
            setWidthImageScrollMulti();
            $('#main').css('cursor', 'default');
            $(button).css('cursor', 'pointer');
            $(button).removeClass('loading');
        });
    }
};

var activeImage = function(menu,num,button){

	if (menu == 0) {
        $('#image-scroll-1 .image img').each(function(){
            if ($(this).parent().hasClass(num) && !$(this).parent().hasClass('off-1')){
			loadImage(this,button);
            }
        });
    }

    if (menu == 1) {
        //alert("si"+menu+num);
        $('#image-scroll-'+num+' .image img').each(function() {
            if (!$(this).parent().hasClass('off-1') && !$(this).parent().hasClass('off-2')){
                loadImage(this,button);
            }
        });
    }

    if (menu == 2) {
        $('div[id^="image-scroll"]').each(function() {
            $(this).find('img').each(function() {
                if ($(this).parent().hasClass(num) && !$(this).parent().hasClass('off-1') && !$(this).parent().hasClass('off-2')){
                    loadImage(this,button);
                }
            });
       });
    }


};

var FirstLoadActivationMenus = function() {
    //activar cuando solo es una imagen o tabla
    if ($('#image-scroll-1 .image').length == 1 ) {
        $('#image-scroll-1 .image').hide().toggleClass("off-1");
        $('#image-scroll-1 .image').show();
        activeImage(1,1,null);
    }

    //activar menu de activacion de varios bloques (menu-0)
    $('.button').each(function() {
        if ($(this).hasClass("1")) {
            $(this).trigger('click');
        }
    });

    //activar menu de activacion de menus dinamicos (menu-0)
    $('.buttonloop').each(function() {
        if ($(this).hasClass("1")) {
            $(this).trigger('click');
            $(this).mouseover();
        }
    });
};

//==============================================================================
//run when DOM is ready

$(document).ready(function() {

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


    // show warning message in some version of IE
// TODO: fix for jquery v2
//    var warningBlock = $("#warning-message");
//    if($.browser.msie && $.browser.version=="6.0"){
//        warningBlock
//            .css("background-color","#DA3030")
//            .css("position", "static")
//            .css("top", "0px")
//            .html("Error: Internet Explorer 6 NO está soportado, actualice o cambie de navegador.")
//            .show()
//    };
//    if($.browser.msie && $.browser.version=="7.0"){
//        warningBlock
//            .css("background-color","#E1BC5F")
//            .html("Advertencia: Internet Explorer 7 NO está soportado, actualice o cambie de navegador.")
//            .show()
//    };



/*    if($.browser.msie && $.browser.version=="8.0"){
        warningBlock
            .css("background-color","#DDD")
            .css("color","#555")
            .html("Advertencia: Internet Explorer 8 no está completamente soportado, actualice o cambie de navegador.")
            .show()
    };*/


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


    //Reajustar los anchos cuando se cambia el tamaño del navegador
    var resizeTimer;
    $(window).resize(function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(setWidthImageScrollMulti, 100);
    });

    //agregar mas tamaño cuando detecta meta-group y meta-subgroup
    if ($(".meta-subgroup")[0]){
        $('#wrap-content').css('min-width',827);
    }



    
    //MENU-CONTENT
    //UN MENU
    //botones de activacion de contenido de un menu
    $('#menu-content > a.button').click(function() {
        if (!$(this).hasClass('loading')) {
            $(this).toggleClass("On"); //activar boton
            var num = $(this).attr('class').split(' ')[1];
            
            if($('#image-scroll-1 .image table').exists()) {
                $('#image-scroll-1 .'+num).toggleClass("off-1");
            } else {
                $('#image-scroll-1 .'+num).hide().toggleClass("off-1");
                activeImage(0,num,this);
            }
            setWidthImageScrollMulti();
        }
    });
    //DOS MENUS
    //botones de activacion de contenido de dos menus, menu1
    $('#menu-content #menu-1 a.button').click(function() {
        if (!$(this).hasClass('loading')) {
            $(this).toggleClass("On"); //activar boton

            var num = $(this).attr('class').split(' ')[1];

            $('#image-scroll-'+num+' div.image').each(function() {
                $(this).hide().toggleClass("off-1");
            });

            activeImage(1,num,this);
            setWidthImageScrollMulti();
        }
    });
    //botones de activacion de contenido de dos menus, menu2
    $('#menu-content #menu-2 a.button').click(function() {
        if (!$(this).hasClass('loading')) {
            $(this).toggleClass("On"); //activar boton

            var num = $(this).attr('class').split(' ')[1];

            $('div[id^="image-scroll"]').each(function() {
                $(this).find('div.image').each(function() {
                    if ($(this).hasClass(num)){
                        $(this).hide().toggleClass("off-2");
                    }
                });
            });

            activeImage(2,num,this);
            if (!$(this).hasClass("On")) {
                setWidthImageScrollMulti();
            }
        }
    });

//    // cambiar color del titulo del meta-group con el mouse encima
//   $('.meta-group').mouseover(function(){
//       $(this).find(".meta-group-title").css('color', '#0d899c');
//   }).mouseleave(function(){
//       $(this).find(".meta-group-title").css('color', '#666');
//   });

    //div clicleables en box-item
    $('.box-item.link').click(function(){
        window.location=$(this).find("a").attr("href");return false;
    });

    //div 'ver' 'descargar' clicleables en box-item
    var oldText = false;
    $('.box-item.box-file').mouseover(function(){
        //mostrar "ver" y "descargar"
        $(this).find(".actions-links").find("span").each(function() {
           $(this).show();
        });
    }).mouseleave(function(){
        //ocultar "ver" y "descargar"
        $(this).find(".actions-links").find("span").each(function() {
            $(this).hide();
        });
    });


    // Maps Colombia
    $('area').mouseover(function(){
        var get_dep_atr = $(this).attr('rel').split(";");
        var map_position = -484*get_dep_atr[0];

        $('#map-dep-colombia').css("background","url('/static/img/maps/dep_colombia.png') "+map_position+"px");
        $('#map_info').html(get_dep_atr[1]); //+"<br>"+get_dep_atr[2]);
    }).mouseout(function(){
        $('#map-dep-colombia').css("background","url('/static/img/maps/dep_colombia.png') 0px");
        $('#map_info').html("")
    });

    // Maps Bogota
    $('area').mouseover(function(){
        var get_dep_atr = $(this).attr('rel').split(";");
        var map_position = -346*get_dep_atr[0];

        $('#map-loc-bogota').css("background","url('/static/img/maps/loc_bogota.png') "+map_position+"px");
        $('#map_info').html(get_dep_atr[1]); //+"<br>"+get_dep_atr[2]);
    }).mouseout(function(){
        $('#map-loc-bogota').css("background","url('/static/img/maps/loc_bogota.png') 0px");
        $('#map_info').html("")
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
        $("#loading").hide();
        $("#content").fadeIn();
        $("#content-footer").fadeIn();
        //set width when page is loaded
        setWidthImageScrollMulti();
    });

});