/* strftime for JavaScript 
   original source: http://pythonwise.blogspot.com/2009/06/strftime-for-javascript.html
   Field description (taken from http://tinyurl.com/65s2qw)

    %a 	Locale’s abbreviated weekday name. 	 
    %A 	Locale’s full weekday name. 	 
    %b 	Locale’s abbreviated month name. 	 
    %B 	Locale’s full month name. 	 
    %c 	Locale’s appropriate date and time representation. 	 
    %d 	Day of the month as a decimal number [01,31]. 	 
    %H 	Hour (24-hour clock) as a decimal number [00,23]. 	 
    %I 	Hour (12-hour clock) as a decimal number [01,12]. 	 
    %j 	Day of the year as a decimal number [001,366]. 	 
    %m 	Month as a decimal number [01,12]. 	 
    %M 	Minute as a decimal number [00,59]. 	 
    %p 	Locale’s equivalent of either AM or PM.
    %S 	Second as a decimal number [00,61].
    %U 	Week number of the year (Sunday as the first day of the week) as a
        decimal number [00,53]. All days in a new year preceding the first
        Sunday are considered to be in week 0.
    %w 	Weekday as a decimal number [0(Sunday),6]. 	 
    %W 	Week number of the year (Monday as the first day of the week) as a
        decimal number [00,53]. All days in a new year preceding the first
        Monday are considered to be in week 0.
    %x 	Locale’s appropriate date representation. 	 
    %X 	Locale’s appropriate time representation. 	 
    %y 	Year without century as a decimal number [00,99]. 	 
    %Y 	Year with century as a decimal number. 	 
    %Z 	Time zone name (no characters if no time zone exists). 	 
    %% 	A literal '%' character.
*/

$.datepicker.strftime = function(format, date) {
    date = date || new Date();
	var locale = $.datepicker._defaults;
	function days(dayno) {return locale.dayNames[dayno];}
	function daysShort(dayno) {return locale.dayNamesShort[dayno];}
	function months(monthno) {return locale.monthNames[monthno];}
	function monthsShort(monthno) {return locale.monthNamesShort[monthno];}
	function zeropad(n, size) {
		n = '' + n; /* Make sure it's a string */
		size = size || 2;
		while (n.length < size) {n = '0' + n;}
		return n;
	}
	function twelve(n) {return (n <= 12) ? n : 24 - n;}
    var fields = {
        a: daysShort(date.getDay()),
        A: days(date.getDay()),
        b: monthsShort(date.getMonth()),
        B: months(date.getMonth()),
        c: date.toString(),
        d: zeropad(date.getDate()),
        H: zeropad(date.getHours()),
        I: zeropad(twelve(date.getHours())),
        /* FIXME: j: */
        m: zeropad(date.getMonth() + 1),
        M: zeropad(date.getMinutes()),
        p: (date.getHours() >= 12) ? 'PM' : 'AM',
        S: zeropad(date.getSeconds()),
        w: zeropad(date.getDay() + 1),
        /* FIXME: W: */
        x: date.toLocaleDateString(),
        X: date.toLocaleTimeString(),
        y: ('' + date.getFullYear()).substr(2, 4),
        Y: '' + date.getFullYear(),
        /* FIXME: Z: */
        '%' : '%'
    };
    var result = '', i = 0;
    while (i < format.length) {
        if (format[i] === '%') {
			var c = format[i + 1];
            result = result + (fields[c]||c);
            ++i;
        }
        else {
            result = result + format[i];
        }
        ++i;
    }
    return result;
}
