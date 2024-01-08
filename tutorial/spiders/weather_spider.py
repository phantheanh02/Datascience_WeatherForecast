from pathlib import Path
from datetime import date, timedelta
import scrapy
import json
import re

class WeatherSpider(scrapy.Spider):
    name = "weather"

    def start_requests(self):
        url = "https://www.worldweatheronline.com/hanoi-weather-history/vn.aspx"
        start_date = date(2019, 1, 1)
        end_date = date(2019, 12, 31)
        delta = timedelta(days=1)
        requestBodys = {
                "__VIEWSTATE": "9+0qwxCyx5jtlEgo4XXOmYCnPixn2XCa2Hx3QtCuManqnvX4Bgd+u0tVGKKkTPYZBflUpJ8vRX8JHUTpFh0X1w2bCekaxMxBaowY9zrpD3mYFzSy",
                "__VIEWSTATEGENERATOR": "F960AAB1",
                "search": "",
                "ctl00$tm1$rblTemp": "1",
                "ctl00$tm1$rblWindSpeed": "2",
                "ctl00$tm1$rblPrecip": "1",
                "ctl00$tm1$rblPressure": "1",
                "ctl00$tm1$rblVis": "1",
                "ctl00$MainContentHolder$txtPastDate": start_date.strftime("%Y-%m-%d"),
                "ctl00$MainContentHolder$butShowPastWeather": "Get Weather",
                "ctl00$hdsample": "",
                "ctl00$hdlat": "10.750",
                "ctl00$hdlon": "106.667",
                "ctl00$areaid": "68415",
                "ctl00$ubu": "1"
        }
        while start_date <= end_date:
            date_filter = start_date.strftime("%Y-%m-%d")
            requestBodys = "__VIEWSTATE=J%2BvyEITQNra7gQN17re0NyFUVg09vzv7McjBI1Jfd13jlRN%2B9DYMSvKssARk2liFzJZ489h6eG0LTqozDk2H%2BmgVis4o%2F2RSqrAxtEyh0c28d%2B5P&__VIEWSTATEGENERATOR=F960AAB1&search=&ctl00%24tm1%24rblTemp=1&ctl00%24tm1%24rblWindSpeed=2&ctl00%24tm1%24rblPrecip=1&ctl00%24tm1%24rblPressure=1&ctl00%24tm1%24rblVis=1&ctl00%24MainContentHolder%24txtPastDate="+date_filter+"&ctl00%24MainContentHolder%24butShowPastWeather=Get+Weather&ctl00%24hdsample=&ctl00%24hdlat=21.033&ctl00%24hdlon=105.850&ctl00%24areaid=68412&ctl00%24ubu=1"
            yield scrapy.Request(url=url, callback=self.parse, method="POST", body=requestBodys, headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}, cb_kwargs={'date': start_date})
            start_date += delta

    def parse(self, response, date):
        filename = f"./data/hanoi/weather_data_2019.csv"
        file1 = open(filename, "a+")

        # Sử dụng css selector để lấy toàn bộ các row trong bảng
        days_details_row = response.selector.css('#aspnetForm > section:nth-child(6) > div > div > div.col.main > div:nth-child(4) > div:nth-child(3) > div > div.days-details > table .days-details-row')
        
        # Bỏ cái header title của table đi
        days_details_row = days_details_row[1:]                                                                                 


        # Loop qua từng row của table
        for row in days_details_row:
            match = re.search(r'rotate\(([\d.]+)deg\)', row.css('td:nth-child(10) > div > svg').attrib["style"])                # Lấy góc của hướng gió  
            direction = ""
            if match:
                rotation_angle = float(match.group(1))
                dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
                ix = round(rotation_angle / (360. / len(dirs)))
                direction = dirs[ix % len(dirs)]                                                                                # Với góc đó thì gió thổi theo hướng nào: Đông, Tây, Nam, Bắc,....
            
            data = {
                'time': row.css('td:nth-child(1) > p.days-comment::text').get(),                                                # Lấy giờ
                'temperature': row.css('td:nth-child(1) > p.days-temp::text').get().replace(" °c", ""),                         # Lấy nhiệt độ
                'month': f"{date.month}",                                                                                       # Lấy tháng
                'feelslike': row.css('td:nth-child(3) > p::text').get().replace(" °c", ""),                                     # Lấy nhiệt độ cảm thấy khi ở ngoài trời
                'wind': row.css('td:nth-child(8) > div.days-wind-number::text').get().replace(" km/h", ""),                     # Lấy tốc độ gió
                'direction': direction,                                                                                         # Lấy hướng gió
                'gust': row.css('td:nth-child(9) > div::text').get().replace(" km/h", ""),                                      # Lấy tốc độ gió giật
                'cloud': row.css('td:nth-child(6)::text').get().replace("%", ""),                                               # Lấy tỷ lệ mây
                'weather': row.css('td:nth-child(2) > img::attr(title)').get(),                                                 # Lấy thông tin kết luận về thời tiết: Có mây, nắng, mưa nhỏ, mưa phùn,...
                'pressure': row.css('td:nth-child(7)::text').get().replace("mb",""),                                            # Lấy áp suất
                'rain': row.css('td:nth-child(4) > div > div.days-rain-number::text').get().replace("mm",""),                   # Lấy lượng mưa
                'rain_ratio': row.css('td:nth-child(5)::text').get().replace("%",""),                                           # Lấy tỷ lệ có mưa
            }

            # Lưu lại data
            file1.write(f"{data['time']};{data['month']};{data['temperature']};{data['feelslike']};{data['wind']};{data['direction']};{data['gust']};{data['cloud']};{data['rain']};{data['rain_ratio']};{data['pressure']};{data['weather']}\n")
            print(data)
        
        
        file1.close()