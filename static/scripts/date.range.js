$(function () {

    $('input[name="date_range"]').daterangepicker({
        "autoApply": true,
        "maxDate": moment(),
        "opens": "left",
        "autoUpdateInput": true,
        "linkedCalendars": false,
        "alwaysShowCalendars": true,
        "locale": {
            "format": 'YYYY-MM-DD',
            "separator": " - ",
            "applyLabel": "Aplicar",
            "cancelLabel": "Cancelar",
            "fromLabel": "De",
            "toLabel": "A",
            "customRangeLabel": "Personalizado",
            "weekLabel": "S",
            "daysOfWeek": [
                "Do",
                "Lu",
                "Ma",
                "Mi",
                "Ju",
                "Vi",
                "Sa"
            ],
            "monthNames": [
                "Enero",
                "Febrero",
                "Marzo",
                "Abril",
                "Mayo",
                "Junio",
                "Julio",
                "Agosto",
                "Septiembre",
                "Octubre",
                "Noviembre",
                "Diciembre"
            ],
            "firstDay": 1
        },
        "ranges": {
            'Hoy': [moment(), moment()],
            'Desde 1 día atrás': [moment().subtract(1, 'days'), moment()],
            'Desde 3 días atrás': [moment().subtract(3, 'days'), moment()],
            'Desde 8 días atrás': [moment().subtract(8, 'days'), moment()],
            'Desde 15 días atrás': [moment().subtract(15, 'days'), moment()],
            'Mes actual': [moment().startOf('month'), moment().endOf('month')],
            'Desde 1 mes atrás': [moment().subtract(1, 'month').startOf('month'), moment()],
            'Desde 2 mes atrás': [moment().subtract(2, 'month').startOf('month'), moment()]
        }
    });

});