import datetime
import vk_api
from vktools import tools
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

    def send_profile_info(self, user_id, item_from_profiles_list):
        name = item_from_profiles_list['name']
        profile_id = item_from_profiles_list['id']
        photos = tools.photos_get(profile_id)
        best_photos = photos[:3]
        self.message_send(user_id, f'Знакомься! {name} - переходи по '
                          f'ссылке: vk.com/id{profile_id}')
        add_users(user_id, profile_id)
        for photo in best_photos:
            own_id = photo['owner_id']
            photo_id = photo['id']
            media = f'photo{own_id}_{photo_id}'
            self.message_send(user_id, f'фото:', media)

    def handler(self):
        offset = 0
        list_of_ids = []
        profiles_list = []
        str_part = ','
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
                    quantity = len(profiles_list)
                    while quantity > 0:
                        item = profiles_list.pop()
                        quantity -= 1
                        if str(item['id']) not in list_of_ids:
                            self.send_profile_info(event.user_id, item)
                            self.message_send(event.user_id,
                                              'Хотите продолжить - введите '
                                              '"далее". Чтобы завершить работу'
                                              ' - введите "стоп".')
                            break
                    else:
                        offset += 20
                        self.message_send(event.user_id,
                                          'Повторите "поиск" ещё раз!')
                elif event.text.lower() == 'далее':
                    quantity = len(profiles_list)
                    while quantity > 0:
                        item = profiles_list.pop()
                        quantity -= 1
                        if str(item['id']) not in list_of_ids:
                            self.send_profile_info(event.user_id, item)
                            self.message_send(event.user_id,
                                              'Хотите продолжить - введите "да'
                                              'лее". Чтобы завершить работу - '
                                              'введите "стоп".')
                            break
                    else:
                        offset += 20
                        self.message_send(event.user_id,
                                          'Повторите "поиск" ещё раз!')
                elif event.text.lower() in ('да', 'нет', '1', '2')\
                        or str_part in event.text.lower():
                    pass
                elif event.text.lower() == 'стоп':
                    break
                else:
                    self.message_send(event.user_id, 'Команда не распознана.'
                                                     'Если хотите найти пару,'
                                                     'введите "поиск".')


if __name__ == '__main__':
    bot = VkBot(bot_token)
    bot.handler()
