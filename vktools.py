import vk_api
from parameters import user_token
from vk_api.exceptions import ApiError


class VkTools():
    def __init__(self, token):
        self.ext_api = vk_api.VkApi(token=token)

    def get_profile_info(self, user_id):

        try:
            info = self.ext_api.method('users.get',
                                       {'user_id': user_id,
                                        'fields': 'bdate,city,sex,relation'
                                        }
                                       )
        except ApiError:
            return

        return info

    def find_city_id(self, city_tittle):

        try:
            ids = self.ext_api.method('database.getCitiesById',
                                      {'fields': 'city_ids'
                                       }
                                      )
        except ApiError:
            return
        id = ids[city_tittle]
        return id

    def user_search(self, city_id, age_from, age_to, sex, offset=None):

        try:
            profiles = self.ext_api.method('users.search',
                                           {'city_id': city_id,
                                            'age_from': age_from,
                                            'age_to': age_to,
                                            'sex': sex,
                                            'status': 6,
                                            'count': 10,
                                            'offset': offset
                                            })
        except ApiError:
            return

        profiles = profiles['items']

        result = []
        for profile in profiles:
            if profile['is_closed'] is False:
                result.append({
                    'name': profile['first_name'] + ' ' + profile['last_name'],
                    'id': profile['id']
                               })

        return result

    def photos_get(self, user_id):
        photos = self.ext_api.method('photos.get',
                                     {'album_id': 'profile',
                                      'owner_id': user_id,
                                      'extended': 1
                                      }
                                     )
        try:
            photos = photos['items']
        except KeyError:
            return

        result = []
        for num, photo in enumerate(photos):
            result.append({'owner_id': photo['owner_id'],
                           'id': photo['id'], 'likes': photo['likes']['count'],
                           'comments': photo['comments']['count']
                           })
            result.sort(key=lambda d: d['likes'])
            result.reverse()
        return result


tools = VkTools(user_token)
