import os
import sys
import math
import requests as rq
import pygame as pg
from random import shuffle

GEO_API_KEY = '40d1649f-0493-4b70-98ba-98533de7710b'
ORG_API_KEY = 'dda3ddba-c9ea-4ead-9010-f43fbc15c6e3'
MAP_SERVER = "http://static-maps.yandex.ru/1.x/"
GEO_SERVER = 'http://geocode-maps.yandex.ru/1.x'
ORG_SERVER = 'https://search-maps.yandex.ru/v1/'


class GeoCodeError(Exception):
    pass


class NotFoundResponseError(GeoCodeError):
    pass


class Map:
    def __init__(self, address=None, coords=None, size=None, mode='map',
                 name='Карта', pt=None, lines=None):
        self.name = name
        params = {'l': mode}
        if pt is not None:
            params['pt'] = '~'.join(pt)
        if lines is not None:
            params['pl'] = '~'.join(lines)
        if address is not None:
            if address.get_form_size() is not None:
                params['spn'] = address.get_form_size()
            params['ll'] = address.get_form_coords()
        if coords is not None:
            params['ll'] = '{},{}'.format(*coords)\
                if not isinstance(coords, str) else coords
        if size is not None:
            params['spn'] = '{},{}'.format(*size)\
                if not isinstance(size, str) else size
        response = rq.get(MAP_SERVER, params=params)
        if not response:
            print("Ошибка выполнения запроса:")
            print(response.url)
            print("Http статус:", response.status_code,
                  "(", response.reason, ")")
            sys.exit(1)

        self.map_name = "map0.png"
        i = 1
        while self.map_name in os.listdir():
            self.map_name = "map{}.png".format(i)
            i += 1
        with open(self.map_name, "wb") as file:
            file.write(response.content)

    def get_map(self):
        return self.map_name

    def get_name(self):
        return self.name

    def remove_self(self):
        os.remove(self.map_name)


class MapShowWindow:
    def __init__(self, *maps, rand=False):
        self.maps = list(maps)
        self.current = 0
        self.fps = 30
        self.running = True
        self.rand = rand

    def run(self):
        pg.init()
        clock = pg.time.Clock()
        pg.display.set_mode((300, 300))
        self.set_map(self.current)

        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.exit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RIGHT:
                        self.current = (self.current + 1) % len(self.maps)
                        self.set_map(self.current)
                        if self.rand:
                            shuffle(self.maps)
            pg.display.flip()
            clock.tick(self.fps)

    def set_map(self, ind):
        map_ = self.maps[ind]
        image = pg.image.load(map_.get_map())
        screen = pg.display.set_mode(image.get_size())
        pg.display.set_caption(map_.get_name())
        screen.blit(image, (0, 0))

    def exit(self):
        self.running = False
        for map_ in self.maps:
            map_.remove_self()


def geocode(address, kind=None):
    params = {'apikey': GEO_API_KEY,
              'geocode': address,
              'format': 'json'}
    if kind is not None:
        params['kind'] = kind
    response = rq.get(GEO_SERVER, params=params)
    if response:
        json_response = response.json()
    else:
        raise GeoCodeError("Ошибка выполнения запроса:\n{}\nHttp статус: \
{} ({}).".format(str(response.url), response.status_code, response.reason))
    feat = json_response['response']['GeoObjectCollection']['featureMember']
    if not feat:
        raise NotFoundResponseError('Геообъект по запросу {} \
не найден.'.format(str(response.url)))
    return feat[0]['GeoObject']


class Address:
    def __init__(self, address, size_coef=1, auto_size=False):
        self.text = address
        self.geo = geocode(address)
        self.coords = [float(i) for i in self.geo['Point']['pos'].split()]

        self.size_coef = size_coef
        self.size = None
        if not auto_size:
            self.set_coef(self.size_coef)

    def get_form_coords(self):
        return '{},{}'.format(*self.coords)

    def get_form_size(self):
        if self.size is None:
            return
        return '{},{}'.format(*self.size)

    def set_coef(self, coef):
        self.size_coef = coef
        env = self.geo['boundedBy']['Envelope']
        l, b = list(map(float, env['lowerCorner'].split()))
        r, t = list(map(float, env['upperCorner'].split()))
        dx = abs(l - r) / 2 * self.size_coef
        dy = abs(b - t) / 2 * self.size_coef
        self.size = [dx, dy]


def make_organisations(type_name, address, results=10):
    params = {
        "apikey": ORG_API_KEY,
        "text": type_name,
        "lang": "ru_RU",
        "ll": address.get_form_coords(),
        "type": "biz",
        'results': results
    }
    response = rq.get(ORG_SERVER, params=params)
    if response:
        json_response = response.json()
    else:
        raise GeoCodeError("Ошибка выполнения запроса:\n{}\nHttp статус: \
{} ({}).".format(str(response.url), response.status_code, response.reason))

    organizations = json_response["features"]
    if not organizations:
        raise NotFoundResponseError('Организаций не найдено.')
    for org in organizations:
        yield Organisation(org)


class Organisation:
    def __init__(self, org_object):
        self.name = org_object["properties"]["CompanyMetaData"]["name"]
        self.address = Address(org_object["properties"]["Company\
MetaData"]["address"])
        self.org_point = "{0},{1}".format(*org_object["geome\
try"]["coordinates"])
        self.work_time = org_object["properties"]["Company\
MetaData"]['Hours']['text']
        avails = org_object["properties"]["CompanyMeta\
Data"]['Hours']['Availabilities'][0]
        self.all_day = None
        if 'TwentyFourHours' in avails.keys():
            self.all_day = 'yes' if avails["TwentyFourHours"] else 'no'

    def get_form_size(self):
        return self.address.get_form_size()

    def get_form_coords(self):
        return self.address.get_form_coords()


def lonlat_distance(a, b):
    degree_to_meters_factor = 111 * 1000
    a_lon, a_lat = a
    b_lon, b_lat = b

    radians_lattitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_lattitude)

    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor
    return math.sqrt(dx * dx + dy * dy)
