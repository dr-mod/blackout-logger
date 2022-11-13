import time
import machine
import ds3231
from micropython import const
from collections import deque
from eink import EPD_3in7

SAVED_TIMESTAMP = const("last_ts.txt")
ON_TIMESTAMP = const("on_ts.txt")
EXPECTED_POWERCUT_FLAG = const("flag.txt")
BLACKOUT_LOG = const("log.txt")


def main():
    ecp = expected_powercut()
    if not ecp:
        log_blackout(read_last_time(), time.time())
        save_on_time()
        print(const("Not expected powercut"))
    save_last_time()
    epd = initial_eink()
    epd.EPD_3IN7_1Gray_init()
    while True:
        save_last_time()
        current = format_full_date(time.time())
        epd.image1Gray.fill_rect(120, 431, 165, 48, epd.white)
        epd.image1Gray.text(current[1], 115, 431, epd.black)
        epd.image1Gray.text(current[0], 115, 447, epd.black)
        epd.EPD_3IN7_1Gray_Display_Part(epd.buffer_1Gray)
        machine.lightsleep(30000)


def display_log(epd):
    try:
        log_entries = tail(BLACKOUT_LOG)
        y = 41
        while True:
            entry = log_entries.popleft().strip()
            epd.image4Gray.text(entry, 15, y, epd.black)
            # epd.image4Gray.text(entry,5, y, epd.darkgray)
            y = y + 16
            print(entry)
    except Exception:
        pass


def format_full_date(time_v):
    w = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    m = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ti = time.localtime(time_v)
    f_date = "%s %02d %s %d " % (w[ti[6]], ti[2], m[ti[1] - 1], ti[0])
    f_time = "%02d:%02d" % (ti[3], ti[4])
    return (f_date, f_time)


def initial_eink():
    epd = EPD_3in7()
    epd.image1Gray.fill(0xff)
    epd.image4Gray.fill(0xff)
    epd.image4Gray.fill_rect(0, 0, 280, 30, epd.black)
    epd.image4Gray.text('Blackouts log', 5, 11, epd.white)
    epd.image4Gray.fill_rect(0, 300, 280, 30, epd.black)
    epd.image4Gray.text('Current session', 5, 311, epd.white)
    # epd.image4Gray.text('GRAY2 with white background', 5, 311, epd.grayish)
    # epd.image4Gray.text('GRAY3 with white background', 5, 341, epd.darkgray)
    # epd.image4Gray.text('GRAY4 with white background', 5, 371, epd.black)
    epd.image4Gray.text('Beginning ->', 5, 341, epd.darkgray)
    epd.image4Gray.text('Last check ->', 5, 431, epd.darkgray)
    on_date_time = format_full_date(read_on_time())
    epd.image4Gray.text(on_date_time[1], 115, 341, epd.black)
    epd.image4Gray.text(on_date_time[0], 115, 357, epd.black)

    display_log(epd)
    epd.EPD_3IN7_4Gray_Display(epd.buffer_4Gray)
    return epd


def tail(filename, n=16):
    d = deque((), n)
    with open(filename) as f:
        for line in f:
            d.append(line)
    return d


def log_blackout(from_time, to_time):
    on_ti = time.localtime(from_time)
    last_ti = time.localtime(to_time)
    entry = "%s - %s\n" % (format_time(on_ti), format_time(last_ti))
    with open(BLACKOUT_LOG, "a") as f:
        f.write(entry)


def format_time(ti):
    return "%02d:%02d:%02d/%02d.%02d" % (ti[3], ti[4], ti[5], ti[2], ti[1])


def init_rtc():
    ds = ds3231.ds3231()
    set_internal_time(ds.read_time())


def set_internal_time(utc_time):
    rtc_base_mem = const(0x4005c000)
    atomic_bitmask_set = const(0x2000)
    (year, month, day, hour, minute, second, wday, yday) = time.localtime(utc_time)
    machine.mem32[rtc_base_mem + 4] = (year << 12) | (month << 8) | day
    machine.mem32[rtc_base_mem + 8] = ((hour << 16) | (minute << 8) | second) | (((wday + 1) % 7) << 24)
    machine.mem32[rtc_base_mem + atomic_bitmask_set + 0xc] = 0x10


def save_last_time():
    save_time(SAVED_TIMESTAMP)


def read_last_time():
    return read_time(SAVED_TIMESTAMP)


def save_on_time():
    save_time(ON_TIMESTAMP)


def read_on_time():
    return read_time(ON_TIMESTAMP)


def read_time(file_name):
    t = 0
    try:
        f = open(file_name, 'r')
        t = int(f.readline())
        f.close()
    except Exception:
        pass
    return t


def save_time(file_name):
    with open(file_name, 'w') as f:
        f.write(str(time.time()))


def expected_powercut():
    t = False
    try:
        with open(EXPECTED_POWERCUT_FLAG, 'r') as f:
            a = int(f.readline())
            if a != 0:
                t = True
    except Exception:
        t = False
    if t:
        with open(EXPECTED_POWERCUT_FLAG, 'w') as f:
            f.write("0")
    return t


init_rtc()
main()
