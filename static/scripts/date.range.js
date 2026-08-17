//  Date range picker configuration
//  https://github.com/longbill/jquery-date-range-picker
//
//  It is responsive: on narrow screens only one month is shown and the picker
//  is rendered as a bottom sheet (see active_fires.css), on wider screens the
//  two classic months are kept.

$(function () {

    // the same breakpoint as the lateral panel: while it is a drawer the picker
    // is shown as a centred sheet (see active_fires.css) with a single month
    var narrow_screen = window.matchMedia ? window.matchMedia("(max-width: 899px)") : null;

    function is_narrow() {
        return narrow_screen ? narrow_screen.matches : false;
    }

    function picker_options() {
        return {
            autoClose: false,
            format: 'YYYY-MM-DD',
            language: 'es',
            separator: ' a ',
            startOfWeek: 'monday',
            getValue: function () {
                if ($('#from-date').val() && $('#to-date').val())
                    return $('#from-date').val() + ' a ' + $('#to-date').val();
                else
                    return '';
            },
            setValue: function (s, s1, s2) {
                $('#from-date').val(s1);
                $('#to-date').val(s2);
            },
            startDate: "2016-01-01",
            endDate: moment().endOf("day"),
            showShortcuts: true,
            customShortcuts: [
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
                    name: '-15 Días',
                    dates: function () {
                        return [moment().subtract(15, 'days').toDate(), moment().toDate()];
                    }
                },
                {
                    name: '-1 Meses',
                    dates: function () {
                        return [moment().subtract(1, 'months').toDate(), moment().toDate()];
                    }
                },
                {
                    name: '-2 Meses',
                    dates: function () {
                        return [moment().subtract(2, 'months').toDate(), moment().toDate()];
                    }
                },
            ],
            monthSelect: true,
            yearSelect: true,
            // one month on phones, two months on tablet/desktop. The two
            // calendars stay independent (stickyMonths off, the plugin
            // default) so a range spanning years can still be picked in one go
            singleMonth: is_narrow(),
        };
    }

    $('#period').dateRangePicker(picker_options());

    // rebuild the picker when the screen crosses the breakpoint (rotation,
    // window resize), keeping the current selection
    function rebuild_picker() {
        var picker = $('#period').data('dateRangePicker');
        var from_date = $('#from-date').val();
        var to_date = $('#to-date').val();
        if (picker && picker.destroy) picker.destroy();
        $('#period').dateRangePicker(picker_options());
        if (from_date && to_date) {
            $('#period').data('dateRangePicker').setDateRange(from_date, to_date, true);
        }
    }

    if (narrow_screen) {
        if (narrow_screen.addEventListener) narrow_screen.addEventListener('change', rebuild_picker);
        else if (narrow_screen.addListener) narrow_screen.addListener(rebuild_picker);
    }

});
