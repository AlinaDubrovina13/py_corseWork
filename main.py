import requests
import time
from tqdm import tqdm
import json


class VK:

    def __init__(self, access_token, user_id, version='5.131', album_id='profile', extended_options='1'):
        self.token = access_token
        self.id = user_id
        self.extended = extended_options
        self.album_id = album_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        response.raise_for_status()
        return response.json()

    def max_size(self, item, name):
        symbols = ['w', 'z', 'y', 'r', 'q', 'p', 'o', 'x', 'm', 's']
        for symbol in symbols:
            for characteristic in item:
                if symbol == characteristic['type']:
                    return {'size': characteristic['type'], 'name': name, 'url': characteristic['url']}

    def photo_max_size(self, response):
        photo_size_list = []
        for item in response['response']['items']:
            photo_size_list.append(self.max_size(item['sizes'], item['likes']['count']))
        return photo_size_list

    def get_photo(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id, 'album_id': self.album_id, 'extended': self.extended}
        response = requests.get(url, params={**self.params, **params})
        response.raise_for_status()
        temp = response.json()
        return self.photo_max_size(temp)


class YaUploader:
    def __init__(self, token: str, number_of_photos=5):
        self.token = token
        self.upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        self.number_of_photos = number_of_photos

    def get_headers(self):
        return {
            'Authorization': f'OAuth {self.token}'
        }

    def ya_dir(self, path):
        ya_dir_url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = path
        headers = self.get_headers()
        response = requests.get(ya_dir_url, headers=headers, params=params)
        if response.status_code != 200:
            print("Создана папка")
            response = requests.put(ya_dir_url, headers=headers, params=params)
        else:
            print("Папка уже создана")
        return response

    def _get_upload_url(self, path):
        params = {"path": f'{path["path"]}/info.json', "overwrite": "true"}
        headers = self.get_headers()
        response = requests.get(self.upload_url, headers=headers, params=params)
        return response.json()

    def mk_json_file(self, file_data_with_url):
        file_data_without_url = []
        for i in range(0, self.number_of_photos):
            file_data_without_url.append({"file_name": f'{file_data_with_url[i]["name"]}.jpg',
                                          "size": file_data_with_url[i]["size"]})
        file = open("info.json", "w")
        json.dump(file_data_without_url, file, ensure_ascii=False, indent=2)
        file.close()

    def upload_json_file(self, path, file_data_with_url):
        self.mk_json_file(file_data_with_url)
        response_dict = self._get_upload_url(path)
        upload_file_url = response_dict.get("href", "")
        with open("info.json", 'rb') as upload_file:
            response = requests.put(upload_file_url, files={"file": upload_file})
            response.raise_for_status()
            if response.status_code == 201:
                print('\r\nФайл успешно создан')

        return response.json

    def range_check(self, url_photo):
        if self.number_of_photos > len(url_photo):
            return len(url_photo)
        else:
            return self.number_of_photos

    def upload(self, id_user):
        url_photo = vk.get_photo()
        headers = self.get_headers()
        path = {"path": f"photo_{id_user}"}
        self.number_of_photos = self.range_check(url_photo)
        self.ya_dir(path).raise_for_status()
        self.upload_json_file(path, url_photo)
        for i in tqdm(range(0, self.number_of_photos)):
            params = {"path": f"{path['path']}/{url_photo[i]['name']}.jpg", "url": f"{url_photo[i]['url']}"}
            response = requests.post(self.upload_url, headers=headers, params=params)
            response.raise_for_status()
            time.sleep(1)
        return '\n Загрузка завершена'


def getting_access():
    getting_access_key = {
        'access_token': input('Введите VK token: '),
        'user_id': input('Введите VK ID пользователя: '),
        'ya_token': input('Введите Yandex token: '),
        'number_of_photos': int(input('Введите количество фотографий: '))
    }

    return getting_access_key


if __name__ == '__main__':
    access_key = getting_access()
    vk = VK(access_key['access_token'], access_key['user_id'])
    user = vk.users_info()
    print(f"Пользователь: {user['response'][0]['first_name']} {user['response'][0]['last_name']}")
    uploader = YaUploader(access_key['ya_token'], access_key['number_of_photos'])
    result = uploader.upload(access_key['user_id'])
    print(result)