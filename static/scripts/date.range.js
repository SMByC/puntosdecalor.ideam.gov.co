$(function () {

    $('#period').dateRangePicker(
	{
        autoClose: false,
	    format: 'YYYY-MM-DD',
        language: 'es',
		separator : ' a ',
        startOfWeek: 'monday',
        getValue: function()
        {
            if ($('#from-date').val() && $('#to-date').val() )
                return $('#from-date').val() + ' a ' + $('#to-date').val();
            else
                return '';
        },
        setValue: function(s,s1,s2)
        {
            $('#from-date').val(s1);
            $('#to-date').val(s2);
        },
        startDate: "2016-01-01",
        endDate: moment().endOf("day"),
        showShortcuts: true,
        customShortcuts :
        [
            {
                name: 'Hoy',
                dates: function () {
                    return [moment().toDate(), moment().toDate()];
                }
            },
            {
                name: '-3 Días',
                dates: function () {
                    return [moment().subtract(3, 'days').toDate(), moment().toDate()];
                }
            },
            {
                name: '-8 Días',
                dates: function () {
                    return [moment().subtract(8, 'days').toDate(), moment().toDate()];
                }
            },
            {
                name: 'Mes actual',
                dates: function () {
                    return [moment().startOf('month').toDate(), moment().toDate()];
                }
            },
            {
                name: '-3 Meses',
                dates: function () {
                    return [moment().subtract(3, 'months').toDate(), moment().toDate()];
                }
            },
            {
                name: 'Año actual',
                dates: function () {
                    return [moment().startOf('year').toDate(), moment().toDate()];
                }
            },
        ],
        monthSelect: true,
        yearSelect: true,
	});

});