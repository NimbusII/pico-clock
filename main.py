from epd2in13 import EPD_2in13
import json
import ada_framebuf
import utime
import os
import random
import time

CHAR_WIDTH_PIXELS = 6
h_landscape = 128;  w_landscape = 250 # e-paper heigth and width. It will be used in landscape mode
        

def load_image(filename):
    with open(filename, 'rb') as f:
        f.readline()
        f.readline()
        width, height = [int(v) for v in f.readline().split()]
        data = bytearray(f.read())
        flipped = bytearray([b ^ 0xFF for b in data])
    return ada_framebuf.FrameBuffer(flipped, width, height, framebuf.MONO_HLSB)

def get_quote(time_string):
    # Opening JSON file
    json_file_names = [filename for filename in os.listdir(".") if filename.endswith('.json')]
    for filename in json_file_names:
        f = open(filename)
        data = json.load(f)
        quotes_list = data.get(time_string)
        f.close()
        del data
        if quotes_list is not None:
            break
    else:
        print("couldn't find anything :( ")
        return None

    quote = random.choice(quotes_list)
    return quote

def str_sanitise(string):
    return string.replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u2014", "--")


def text_wrap(string,width,height):
    cols = width // CHAR_WIDTH_PIXELS # 30, in my case
    output_lines = []
    
    split = string.split()
    line_num=0
    # keep going until all words are exhausted
    while len(split) > 0:
        this_line = ''
        # add words to this line until no space for next word
        while len(split[0]) < (cols - len(this_line)):             
            this_line += (split.pop(0) + ' ')
            if len(split) == 0:
                break
            
        #this line is full
        this_line = this_line[:-1] # remove trailing space
        output_lines.append(this_line)
        line_num += 1
        if line_num > height/12:
            print('oh nooo the quote is too long')
            
    return output_lines
    
        
if __name__=='__main__':
            

    def load_quote(current_time):
        quote = get_quote(current_time)
        if quote is None:
            string = f"No quote for time {current_time}, so I'm returning a test message. TODO: check surrounding approximate times"
            attribution = " - sadness"
        else:
            string = str_sanitise(quote.get("prefix") + quote.get("time") + quote.get("suffix"))
            attribution = f"- {quote.get("author")}, {quote.get("book")}"
            
        print(string)
        print(attribution)
        return (string, attribution)

    def display(string, attribution):
        buf  = bytearray(w_landscape * h_landscape // 8) # used by frame buffer (landscape)
        fb = ada_framebuf.FrameBuffer(buf, w_landscape, h_landscape, ada_framebuf.MVLSB)
        fb.fill(0xff)
        
        lines = text_wrap(string, width=248, height=112)
        for line_num, line in enumerate(lines):
            fb.text(line, 1, 8 + line_num * 12, 0)
        
        start_at = 248 - CHAR_WIDTH_PIXELS*len(attribution)
        fb.text(attribution, start_at, 120, 0)

        epd.display_landscape(buf)
        epd.delay_ms(1000)
        
    
    epd = EPD_2in13()
    rtc=machine.RTC()
  
    displayed_time = ''
    ts=rtc.datetime()
    hours, mins = ts[4:6]    
    current_time = f"{hours:02d}:{mins:02d}"
    string = f'This is a placeholder quote which displays for up to 60s during startup, as I didn\'t add in functionality for preloading a quote for the first discovered time. The current time is {current_time}'
    attribution = '- Abigail, 19/11/23'
    
    while True:
        ts=rtc.datetime()
        hours, mins = ts[4:6]    
        current_time = f"{hours:02d}:{mins:02d}"
        
        if current_time != displayed_time:
            print(f"time has changed, updating to display {current_time}")
            # time has changed. Display the pre-loaded image, and prep for the next min
            display(string, attribution)
            displayed_time = current_time
            
            #preload next minute's quote
            future_time = time.mktime((ts[0], ts[1], ts[2], ts[3], ts[4], ts[5]+1, ts[6], ts[7]))
            hours, mins = time.localtime(future_time)[4:6]
            next_time = f"{hours:02d}:{mins:02d}"
            print(f"loading quote for next timestamp: {next_time}")
            string, attribution = load_quote(next_time)
            
        utime.sleep(5)
