$(document).ready(function () {
    //Reset all form
    $('select').val($("#target option:first").val());

    // auto change width based on content
    var realWidth = $('#content').width();

    if (realWidth > $('#wrap-content').width()){
        $('#wrap-content').css("width",realWidth+5);
    }


    //*****************************input
    //Parametro y Escenarios
    //*****************************     
    $("#id_Escenarios").hide();
    $("label[for='id_Escenarios']").html("");

    $("#id_Variable").change(function (e) {
        $("label[for='id_Escenarios']").html("Escenario:");

        $.ajax({
            type: "POST",
            url: "ajax/parametro/",
            data: {t_parameters: $(this).val()},
            success: function (data, text, xhrobject) {
                // uncomment if you wanna to see objects on firebug console
                //console.log(data,text,xhrobject)
                $("#id_Escenarios").children().remove()
                $("#id_Escenarios").append("<option selected=\"selected\" value=\"\">------</option>")
                for (i in data) {
                    i = data[i]
                    $("#id_Escenarios").append(
                        "<option value=\"" + i.id + "\">" + i.name + "</option>"
                    )
                }
            },
            crossDomain: false
        });


        $("#id_Escenarios").show();
        $("#id_catalogo").hide();
    });
    //*************************************************
    //Consulta por codigo, municipio, depto, corriente
    //*************************************************         
    $("#id_catalogo").hide();
    $("#id_Region").hide();
    $("label[for='id_catalogo']").html("");

    $("#id_consulta").change(function (e) {
        //Debe ser diferente para la opciion de Colombia
        if ($("#id_consulta option:selected").text() == "Colombia") {
            $("#id_catalogo").hide();
            $("label[for='id_catalogo']").html("");
        }
        else {
            $("#id_catalogo").hide();
            $("#id_Region").hide();
            $("label[for='id_catalogo']").html($("#id_consulta option:selected").text());
            //codigo =$("#id_consulta option:selected").text() 

            $.post(
                // url to post
                "ajax/catalogo/",
                // args
                { Catalogo2: $('#id_Variable option:selected').text(), Consulta2: $("#id_consulta option:selected").text(), escenariosC: $("#id_Escenarios option:selected").text()},
                // response callback
                function (data, text, xhrobject) {
                    // uncommen/reportes/t if you wanna to see objects on firebug console
                    //console.log(data, text, xhrobject)
                    $("#id_catalogo").children().remove()
                    $("#id_catalogo").append("<option checked=\"checked\" value=\"\">------</option>")
                    for (i in data) {
                        i = data[i]
                        $("#id_catalogo").append("<option value=\"" + i.id + "\">" + i.name + "</option>")
                    }
                })

            $("#id_catalogo").show();
        }
        ;
    });
    //************************************
    //Periodo: Anual, Mensual, Trimestral
    //************************************
    $("#id_Meses").hide();
    $("label[for='id_Meses']").html("");
    $("#id_Trimestre").hide();
    $("label[for='id_Trimestre']").html("");

    $("#id_Periodo").change(function (e) {
        //selecciono ANUAL
        if ($("#id_Periodo option:selected").text() == "Anual") {
            $("#id_Trimestre").hide();
            $("#id_Meses").hide();
            $("label[for='id_Trimestre']").html("");
            $("label[for='id_Meses']").html("");
        }
        //Selecciono MENSUAL
        if ($("#id_Periodo option:selected").text() == "Mensual") {
            $("#id_Trimestre").hide();
            $("label[for='id_Trimestre']").html("");
            $("label[for='id_Meses']").html($("#id_Periodo option:selected").text());
            $.post(
                // url to post
                "ajax/periodo_meses/",
                // args
                //$("#id_periodo option:selected").text(),
                { type_period: $('#id_Periodo option:selected').text()},
                // response callback

                function (data, text, xhrobject) {
                    // uncomment if you wanna to see objects on firebug console
                    //console.log(data,text,xhrobject)

                    $("#id_Meses").children().remove()
                    $("#id_Meses").append("<option selected=\"selected\" value=\"\">------</option>")
                    for (i in data) {
                        i = data[i]
                        $("#id_Meses").append(
                            "<option value=\"" + i.id + "\">" + i.name + "</option>"
                        )
                    }
                });
            $("#id_Meses").show();
        }
//Selecciono TRIMESTRE  //Consulta por codigo, municipio, depto, corriente
        //*************************************************
        if ($("#id_Periodo option:selected").text() == "Trimestral") {
            $("#id_Meses").hide();
            $("label[for='id_Meses']").html("");
            $("label[for='id_Trimestre']").html($("#id_Periodo option:selected").text());
            $.post(
                // url to post
                "ajax/periodo_trimestre/",
                // args
                { type_period: $('#id_Periodo option:selected').text()},
                // response callback
                function (data, text, xhrobject) {
                    // uncomment if you wanna to see objects on firebug console
                    // console.log(data,text,xhrobject)
                    $("#id_Trimestre").children().remove()
                    $("#id_Trimestre").append("<option selected=\"selected\" value=\"\">------</option>")
                    for (i in data) {
                        i = data[i]
                        $("#id_Trimestre").append("<option value=\"" + i.id + "\">" + i.name + "</option>")
                    }
                }
            );
            $("#id_Trimestre").show();
            $("#id_Trimestre").show();
        }
    });
    //**********************************************************************************************
    //Periodo Inicial Clima presente
    //**********************************************************************************************
    $("#id_anio_Inicio_cp").hide();
    $("label[for='id_anio_Inicio_cp']").html("");
    $("#id_Escenarios").change(function (e) {
        //Selecciono RCP
        escenarios = $("#id_Escenarios option:selected").text();
        //esc = escenarios.substr(0,3);
        $("label[for='id_anio_Inicio_cp']").html("Periodo inicial C.presente :");
        //alert(esc);
        $.post(
            // url to post
            "ajax/anioIni_cp/",
            { escenario1: $("#id_Escenarios option:selected").text()},
            // response callback         $(this).val()
            function (data, text, xhrobject) {
                // uncomment if you wanna to see objects on firebug console
                //console.log(data,text,xhrobject)
                $("#id_anio_Inicio_cp").children().remove()
                $("#id_anio_Inicio_cp").append("<option selected=\"selected\" value=\"\">------</option>")
                for (i in data) {
                    i = data[i]
                    $("#id_anio_Inicio_cp").append("<option value=\"" + i.id + "\">" + i.name + "</option>")
                }
            }
        );
        $("#id_anio_Inicio_cp").show();
    });
    //**********************************************************************************************
    //Periodo Final Clima presente
    //****************************************************************************
    $("#id_anio_Final_cp").hide();
    $("label[for='id_anio_Final_cp']").html("");
    $("#id_anio_Inicio_cp").change(function (e) {
        $("label[for='id_anio_Final_cp']").html("Periodo final C.presente :");
        $.post(
            // url to pos<h3>Estas etiquetas van en <i>azul y negrita</i></h3>t
            "ajax/anioFin_cp/",
            // args
            {t_desde1: $("#id_anio_Inicio_cp option:selected").text(), escenario1: $("#id_Escenarios option:selected").text()},
            // response callback
            function (data, text, xhrobject) {
                // uncomment if you wanna to see objects on firebug console
                //console.log(data,text,xhrobject)
                $("#id_anio_Final_cp").children().remove()
                $("#id_anio_Final_cp").append("<option selected=\"selected\" value=\"\">------</option>")
                for (i in data) {
                    i = data[i]
                    $("#id_anio_Final_cp").append("<option value=\"" + i.id + "\">" + i.name + "</option>")
                }
            }
        );
        $("#id_anio_Final_cp").show();
    });
    //**********************************************************************************************
    //Periodo Inicial, clima futuro
    //**********************************************************************************************
    $("#id_anio_Inicial").hide();
    $("label[for='id_anio_Inicial']").html("");
    $("#id_Escenarios").change(function (e) {
        //Selecciono RCP
        escenarios = $("#id_Escenarios option:selected").text();
        //esc = escenarios.substr(0,3);
        $("label[for='id_anio_Inicial']").html("Periodo inicial C.futuro :");
        //alert(esc);
        $.post(
            // url to post
            "ajax/anioInicio/",
            { escenario2: $("#id_Escenarios option:selected").text()},
            // response callback         $(this).val()
            function (data, text, xhrobject) {
                // uncomment if you wanna to see objects on firebug console
                //console.log(data,text,xhrobject)
                $("#id_anio_Inicial").children().remove()
                $("#id_anio_Inicial").append("<option selected=\"selected\" value=\"\">------</option>")
                for (i in data) {
                    i = data[i]
                    $("#id_anio_Inicial").append("<option value=\"" + i.id + "\">" + i.name + "</option>")
                }
            }
        );
        $("#id_anio_Inicial").show();
    });
    //**********************************************************************************************
    //Periodo Final, clima futuro
    //****************************************************************************
    $("#id_anio_Final").hide();
    $("label[for='id_anio_Final']").html("");
    $("#id_anio_Inicial").change(function (e) {
        $("label[for='id_anio_Final']").html("Periodo final C.futuro :");
        $.post(
            // url to pos<h3>Estas etiquetas van en <i>azul y negrita</i></h3>t
            "ajax/anioFinal/",
            // args
            {t_desde2: $("#id_anio_Inicial option:selected").text(), escenario2: $("#id_Escenarios option:selected").text()},
            // response callback
            function (data, text, xhrobject) {
                // uncomment if you wanna to see objects on firebug console
                $("#id_anio_Final").children().remove()
                $("#id_anio_Final").append("<option selected=\"selected\" value=\"\">------</option>")
                for (i in data) {
                    i = data[i]
                    $("#id_anio_Final").append("<option value=\"" + i.id + "\">" + i.name + "</option>")
                }
            }
        );
        $("#id_anio_Final").show();
    });
});
