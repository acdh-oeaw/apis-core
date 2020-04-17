import math
import re
from datetime import datetime, timedelta


def parse_date( date_string: str ) -> (datetime, datetime, datetime):
    """
    function to parse a string date field of an entity

    :param date_string : str :
        the field value passed by a user

    :return date_single : datetime :
        single date which represents either the precise date given by user or median in between a range.

    :return date_ab : datetime :
        starting date of a range if user passed a range value either implicit or explicit.

    :return date_bis : datetime :
        ending date of a range if user passed a range value either implicit or explicit.
    """


    def parse_date_range_individual(date, ab=False, bis=False):
        """
        As a sub function to parse_date, this function parse_date_individual handles a very single date since
        in a text field a user can pass multiple dates.


        :param date : str :
            recognized sub string which potentially is a date (in julian calendar format)

        :param ab : boolean : optional
            indicates if a single date shall be intepreted as a starting date of a range

        :param bis : boolean : optional
            indicates if a single date shall be intepreted as an ending date of a range


        :return tuple (datetime, datetime) :
            two datetime objects representing the dates.
            Two indicate that an implicit single date range was given (e.g. a year without months or days).
            Has to be further processed then since it can be either a starting or ending date range.
        or
        :return datetime :
            One datetime object representing the date.
            if a single date was given.
        """


        def get_last_day_of_month(month, year):
            """
            Helper function to return the last day of a given month and year (respecting leap years)

            :param month : int

            :param year : int

            :return day : int
            """

            if month in [1, 3, 5, 7, 8, 10, 12]:
                # 31 day months
                return 31
            elif month in [4, 6, 9, 11]:
                # 30 day months
                return 30
            elif month == 2:
                # special case february, differentiate leap years with respect to gregorian leap rules
                if year % 4 == 0:
                    if year % 100 == 0:
                        if year % 400 == 0:
                            # divisible by 4, by 100, by 400
                            # thus is leap year
                            return 29
                        else:
                            # divisible by 4, by 100, not by 400
                            # thus is not leap yar
                            return 28
                    else:
                        # divisible by 4, not by 100, if by 400 doesn't matter
                        # thus is leap year
                        return 29
                else:
                    # not divisible by 4, if by 100 or by 400 doesn't matter
                    return 28
            else:
                # no valid month
                raise ValueError("Month " + str(month) + " does not exist.")



        # replace all kinds of delimiters
        date = date.replace(" ", "").replace("-", ".").replace("/", ".").replace("\\", ".")

        # parse into variables for use later
        year = None
        month = None
        day = None

        # check for all kind of Y-M-D combinations
        if re.match(r"\d{3,4}$", date):
            # year
            year = int(date)

        elif re.match(r"\d{1,2}\.\d{3,4}$", date):
            # month - year
            tmp = re.split(r"\.", date)
            month = int(tmp[0])
            year = int(tmp[1])

        elif re.match(r"\d{1,2}\.\d{1,2}\.\d{3,4}$", date):
            # day - month - year
            tmp = re.split(r"\.", date)
            day = int(tmp[0])
            month = int(tmp[1])
            year = int(tmp[2])

        elif re.match(r"\d{3,4}\.\d{1,2}\.?$", date):
            # year - month
            tmp = re.split(r"\.", date)
            year = int(tmp[0])
            month = int(tmp[1])

        elif re.match(r"\d{3,4}\.\d{1,2}\.\d{1,2}\.?$", date):
            # year - month - day
            tmp = re.split(r"\.", date)
            year = int(tmp[0])
            month = int(tmp[1])
            day = int(tmp[2])
        else:
            # No sensical interpretation found
            raise ValueError("Could not interpret date.")


        if (ab and bis) or year is None:
            # both ab and bis in one single date are not valid, neither is the absence of a year.
            raise ValueError("Could not interpret date.")

        elif not ab and not bis and (month is None or day is None):
            # if both ab and bis are False and either month or day is empty, then it was given
            # an implicit date range (range of all months if given a year or all days if given a month)

            # construct implicit month range
            if month is None:
                month_ab = 1
                month_bis = 12
            else:
                month_ab = month
                month_bis = month

            # construct implicit day range
            if day is None:
                day_ab = 1
                day_bis = get_last_day_of_month(month_bis, year)
            else:
                day_ab = day
                day_bis = day


            # return a tuple from a single date (which the calling function has to further process)
            return (
                datetime(year=year, month=month_ab, day=day_ab),
                datetime(year=year, month=month_bis, day=day_bis)
            )

        else:
            # Either ab or bis is True. Then use the respective beginning or end of range and construct a precise date
            # Or both ab and bis are False. Then construct a precise date from parsed values

            # construct implicit month range if month is None
            if month is None:
                if ab and not bis:
                    # is a starting date, thus take first month of year
                    month = 1
                elif not ab and bis:
                    # is an ending date, thus take last month of year
                    month = 12

            # construct implicit day range if day is None
            if day is None:
                if ab and not bis:
                    # is a starting date, thus take first day of month
                    day = 1
                elif not ab and bis:
                    # is an ending date, thus take last month of year
                    day = get_last_day_of_month(month=month, year=year)

            return datetime(year=year, month=month, day=day)


    try:

        # return variables
        date_single = None
        date_ab = None
        date_bis = None

        # split for angle brackets, check if explicit iso date is contained within them
        date_split_angle = re.split(r"(<.*?>)", date_string)


        if len(date_split_angle) > 1:
            # date string contains angle brackets. Parse them, ignore the rest

            def parse_iso_date(date_string):
                date_string_split = date_string.split("-")
                try:
                    return datetime(year=int(date_string_split[0]), month=int(date_string_split[1]), day=int(date_string_split[2]) )
                except:
                    raise ValueError("Invalid iso date: ", date_string)

            if len(date_split_angle) > 3:
                # invalid case
                raise ValueError("Too many angle brackets.")

            elif len(date_split_angle) == 3:
                # the right amount of substrings, indicating exactly one pair of angle brackets.
                # Parse the iso date in between

                # remove angle brackets and split by commas
                dates_iso = date_split_angle[1][1:-1]

                # check for commas, which would indicate that either one iso date or three are being input
                dates_iso = dates_iso.split(",")
                if len(dates_iso) != 1 and len(dates_iso) != 3:
                    # only either one iso date or three are allowed
                    raise ValueError(
                        "Incorrect number of dates given. Within angle brackets only one or three (separated by commas) are allowed.")

                elif len(dates_iso) == 3:
                    # three iso dates indicate further start and end dates

                    # parse start date
                    date_ab_string = dates_iso[1].strip()
                    if date_ab_string != "":
                        date_ab = parse_iso_date(date_ab_string)

                    # parse end date
                    date_bis_string = dates_iso[2].strip()
                    if date_bis_string != "":
                        date_bis = parse_iso_date(date_bis_string)

                # parse single date
                date_single_string = dates_iso[0].strip()
                if date_single_string != "":
                    date_single = parse_iso_date(date_single_string)


        else:
            # date string contains no angle brackets. Interpret the possible date formats
            date_string = date_string.lower()
            date_string = date_string.replace(" ", "")

            # helper variables for the following loop
            found_ab = False
            found_bis = False
            found_single = False

            # split by allowed keywords 'ab' and 'bis' and iterate over them
            date_split_ab_bis = re.split(r"(ab|bis)", date_string)
            for i, v in enumerate(date_split_ab_bis):

                if v == "ab":
                    # indicates that the next value must be a start date

                    if found_ab or found_single:
                        # if already found a ab_date or single date before then there is non-conformative redundancy
                        raise ValueError("Redundant dates found.")
                    found_ab = True

                    # parse the next value which must be a parsable date string
                    date_ab = parse_date_range_individual(date_split_ab_bis[i + 1], ab=True)

                elif v == "bis":
                    # indicates that the next value must be an end date

                    if found_bis or found_single:
                        # if already found a bis_date or single date before then there is non-conformative redundancy
                        raise ValueError("Redundant dates found.")
                    found_bis = True

                    # parse the next value which must be a parsable date string
                    date_bis = parse_date_range_individual(date_split_ab_bis[i + 1], bis=True)

                elif v != "" and not found_ab and not found_bis and not found_single:
                    # indicates that this value must be a date

                    found_single = True

                    # parse the this value which must be a parsable date string
                    date_single = parse_date_range_individual(v)

                    if type(date_single) is tuple:
                        #  if result of parse_date_range_individual is a tuple then the date was an implict range.
                        #  Then split it into start and end dates
                        date_ab = date_single[0]
                        date_bis = date_single[1]

            if date_ab and date_bis:
                # date is a range

                if date_ab > date_bis:
                    raise ValueError("'ab-date' must be before 'bis-date' in time")

                # calculate difference between start and end date of range,
                # and use it to calculate a single date for usage as median.
                days_delta_half = math.floor((date_bis - date_ab).days / 2, )
                date_single = date_ab + timedelta(days=days_delta_half)

            elif date_ab is not None and date_bis is None:
                # date is only the start of a range, save it also as the single date

                date_single = date_ab

            elif date_ab is None and date_bis is not None:
                # date is only the end of a range, save it also as the single date

                date_single = date_bis

    except Exception as e:
        print("Could not parse date: '", date_string, "' due to error: ", e)

    return date_single, date_ab, date_bis



def get_date_help_text_from_dates(single_date, single_start_date, single_end_date, single_date_written):
    """
    function for creating string help text from parsed dates, to provide feedback to the user
    about the parsing status of a given date field.

    :param single_date: datetime :
        the individual date point

    :param single_start_date: datetime :
        the start range of a date

    :param single_end_date: datetime :
        the endrange of a date

    :param single_date_written: str :
        the textual user entry of a date field (needed to check if empty or not)

    :return help_text: str :
        The text to be displayed underneath a date field, informing the user about the parsing result
    """


    # check which of the dates could be parsed to construct the relevant feedback text

    help_text = ""
    if single_date:
        # single date could be parsed

        help_text = "Date interpreted as "

        if single_start_date or single_end_date:
            # date has also start or end ranges, then ignore single date

            if single_start_date:
                # date has start range

                help_text += \
                    str(single_start_date.year) + "-" + \
                    str(single_start_date.month) + "-" + \
                    str(single_start_date.day) + " until "

            else:
                # date has no start range, then write "undefined"

                help_text += "undefined start until "

            if single_end_date:
                # date has end range

                help_text += \
                    str(single_end_date.year) + "-" + \
                    str(single_end_date.month) + "-" + \
                    str(single_end_date.day)

            else:
                # date has no start range, then write "undefined"

                help_text += "undefined end"

        else:
            # date has no start nor end range. Use single date then.

            help_text += \
                str(single_date.year) + "-" + \
                str(single_date.month) + "-" + \
                str(single_date.day)

    elif single_date_written is not None:
        # date input field is not empty but it could not be parsed either. Show parsing info and help text

        help_text = "<b>Date could not be interpreted</b><br>" + get_date_help_text_default()

    else:
        # date field is completely empty. Show help text only

        help_text = get_date_help_text_default()

    return help_text



def get_date_help_text_default():

    return "Dates are interpreted by defined rules. If this fails, an iso-date can be explicitly set with '&lt;YYYY-MM-DD&gt;'."
