
$(function()
{
    $('#date-range').dateRangePicker({
        language: 'es',
        startOfWeek: 'monday',
        endDate: moment(),
        getValue: function()
        {
            if ($('#id_from_date').val() && $('#id_to_date').val() )
                return $('#id_from_date').val() + ' to ' + $('#id_to_date').val();
            else
                return '';
        },
        setValue: function(s,s1,s2)
        {
            $('#id_from_date').val(s1);
            $('#id_to_date').val(s2);
        },
        showShortcuts: true,
	    shortcuts : null,
        customShortcuts:
	    [
            // today
            {
                name: 'Hoy',
                dates : function()
                {
                    var start = moment().toDate();
                    var end = moment().toDate();
                    return [start,end];
                }
            },
            // 1 dias
            {
                name: '1Días',
                dates : function()
                {
                    var start = moment().subtract(1, 'day').toDate();
                    var end = moment().toDate();
                    return [start,end];
                }
            },
            // 2 dias
            {
                name: '2Días',
                dates : function()
                {
                    var start = moment().subtract(2, 'day').toDate();
                    var end = moment().toDate();
                    return [start,end];
                }
            },
            // 3 dias
            {
                name: '3Días',
                dates : function()
                {
                    var start = moment().subtract(3, 'day').toDate();
                    var end = moment().toDate();
                    return [start,end];
                }
            },
            // 8 dias
            {
                name: '8Días',
                dates : function()
                {
                    var start = moment().subtract(8, 'day').toDate();
                    var end = moment().toDate();
                    return [start,end];
                }
            },
            // mes actual
            {
                name: 'MesActual',
                dates : function()
                {
                    var start = moment().date(0).add(1, 'day').toDate();
                    var end = moment().toDate();
                    return [start,end];
                }
            }
	    ]
        
    })
    .bind('datepicker-open', function() {
        // adjust position
        var elem = $('#date-range');
        $('.date-picker-wrapper').css({
            position: 'absolute',
            top: '' + (elem.offset().top + 23) + 'px',
            // left: '' + (elem.offset().left - 210) + 'px'
            left: 'auto',
            right: '7px'
        });
        
    })
});
