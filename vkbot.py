import datetime
from vktools import *
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from db import create_db, add_users, select_viewed_id
from parameters import bot_token


class VkBot:

    def __init__(self, token):
        self.bot = vk_api.VkApi(token=token)

    def message_send(self, user_id, message=None, attachment=None):
        self.bot.method('messages.send',
                        {'user_id': user_id,
                         'message': message,
                         'random_id': get_random_id(),
                         'attachment': attachment
                         }
                        )

    def get_sex_for_search(self, sex):
        required_sex = 0
        if sex == 1:
            required_sex = 2
        elif sex == 2:
            required_sex = 1
        else:
            longpull = VkLongPoll(self.bot)
            for event in longpull.listen():
                self.message_send(event.user_id,
                                  'Если Вы ищете женщину,'
                                  'введите "1", если мужчину - "2".')
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    required_sex = int(event.text)
        return required_sex

    def get_city_for_search(self, user_id, dict_info):
        longpull = VkLongPoll(self.bot)
        key = 'city'
        if key in dict_info.keys():
            city_id = dict_info['city']['id']
            return city_id
        else:
            self.message_send(user_id, 'Введите название города,'
                                       'в котором ищете пару.')
            for event in longpull.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    city_tittle = event.text.capitalize()
                    city_id = tools.find_city_id(city_tittle)
                    return city_id

    def get_age_for_search(self, birth_date):
        longpull = VkLongPoll(self.bot)
        for event in longpull.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'да' and 8 <= len(birth_date) <= 10:
                    year = int(birth_date[-4:])
                    low_age = datetime.date.today().year - year - 3
                    high_age = datetime.date.today().year - year + 3
                    return low_age, high_age
                elif event.text.lower() == 'нет' or len(birth_date) < 8:
                    self.message_send(event.user_id,
                                      'Последовательно введите нижнюю и верхнюю'
                                      ' границы искомого возраста для пары '
                                      'через запятую.')
                    for event in longpull.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            str_age = event.text
                            ages = str_age.split(',')
                            low_age = ages[0]
                            high_age = ages[1]
                            return low_age, high_age

    def handler(self):
        offset = 0
        list_of_ids = []
        longpull = VkLongPoll(self.bot)
        for event in longpull.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    self.message_send(event.user_id,
                                      'Приветствую. Хотите знакомиться? '
                                      'Если да, введите "поиск".')
                elif event.text.lower() == 'поиск':
                    info = tools.get_profile_info(event.user_id)
                    main_info = info[0]
                    sex = self.get_sex_for_search(main_info['sex'])
                    id_of_city = self.get_city_for_search(event.user_id,
                                                          main_info)
                    self.message_send(event.user_id, 'Бот будет искать пару '
                                                     'примерно вашего возраста '
                                                     '(в диапазоне +3/-3 года).'
                                                     ' Если условия поиска вам '
                                                     'подходят, введите "да", '
                                                     'или "нет" - если хотите '
                                                     'ввести свой диапазон.')
                    age_tuple = self.get_age_for_search(main_info['bdate'])
                    low_age = age_tuple[0]
                    high_age = age_tuple[1]
                    profiles_list = tools.user_search(id_of_city,
                                                      low_age, high_age,
                                                      sex, offset)
                    create_db()
                    list_of_ids = list_of_ids + select_viewed_id(event.user_id)
                    for item in profiles_list:
                        name = item['name']
                        id = item['id']
                        if id in list_of_ids:
                            continue
                        else:
                            photos = tools.photos_get(id)
                            best_photos = photos[:3]
                            self.message_send(event.user_id,
                                              f'Знакомься! {name} - переходи по'
                                              f'ссылке: vk.com/id{id}')
                            add_users(event.user_id, id)
                            for photo in best_photos:
                                own_id = photo['owner_id']
                                photo_id = photo['id']
                                media = f'photo{own_id}_{photo_id}'
                                self.message_send(event.user_id,
                                                  f'фото:', media)
                    self.message_send(event.user_id,
                                      'Хотите продолжить - введите "поиск"'
                                      'ешё раз! Чтобы завершить работу - '
                                      'введите "стоп".')
                    offset += 10
                elif event.text.lower() == ('да', 'нет', '1', '2'):
                    continue
                elif event.text.lower() == 'стоп':
                    break
                else:
                    self.message_send(event.user_id, 'Команда не распознана.'
                                                     'Если хотите найти пару,'
                                                     'введите "поиск".')


if __name__ == '__main__':
    bot = VkBot(bot_token)
    bot.handler()
