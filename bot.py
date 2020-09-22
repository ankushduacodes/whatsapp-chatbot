import json
import os
import requests
import datetime
import csv
import re

import random
import string


class Bot():
    def __init__(self, json):
        self.json = json
        self.dict_messages = self.json['messages']
        self.APIUrl = os.getenv('APIUrl')
        self.token = os.getenv('token')
        # self.token = ''

    def send_requests(self, method, data):
        url = f"{self.APIUrl}{method}?token={self.token}"
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        return response.json()

    def send_message(self, chatID, text):
        data = {
            'chatId': chatID,
            'body': text
        }
        answer = self.send_requests('sendMessage', data)
        return answer

    def welcome_user(self, chatID, text):
        return self.send_message(chatID, text)

    def ask_next_question(self, chatID, text):
        return self.send_message(chatID, text)

    def confirm_reservation(self, chatID, string):
        path = '/home/ankushduacodes/pythonanywhere/orders/'+chatID+'_ongoing.json'
        with open(path, mode='r') as f:
            user = json.load(f)
        text = f"""Restaurant's Name = *{user.get('rstrnt_choice')}*\nDate of Booking = *{user.get('date_of_booking')}*\nTime of arrival = *{user.get('eta')}*\nReservation is for *{user.get('ppl_count')}*\nYour Details are:\n*{user.get('full_name_and_enter_phn_number')[0]}\n{user.get('full_name_and_enter_phn_number')[1]}*\n\nWould you like to continue with your reservation?\n\nPlease reply with Yes or No"""
        if string:
            text = string + text
        return self.send_message(chatID, text)

    def send_confirmation(self, chatID):
        text = f"""
        *_Congratulations_*\nYour Reservation was Successful\nThank You for using our Services.
        """
        return self.send_message(chatID, text)

    def confirm_cancellation(self, chatID):
        return self.send_message(chatID, "Are you sure you want to cancel the reservation?")

    def send_goodbye(self, chatID):
        text = "Your reservation was discarded, Thank you for choosing us"
        return self.send_message(chatID, text)

    def processing(self):
        if self.dict_messages:
            for message in self.dict_messages:
                text = message['body']
                id = message['chatId']
                if not message['fromMe']:
                    question_dict = {}
                    with open("/home/ankushduacodes/pythonanywhere/Question_list.csv", mode='r') as f:
                        reader = csv.reader(f)
                        question_dict = {rows[0]: rows[1].replace(
                            '\\n', '\n') for rows in reader}
                    keys = list(question_dict.keys())
                    path = '/home/ankushduacodes/pythonanywhere/orders/' + id + '_ongoing.json'
                    state_dict = {}
                    if not os.path.isfile(path):
                        state_dict['id'] = id
                        state_dict['state'] = keys[1]
                        with open(path, mode='w+') as f:
                            json.dump(state_dict, f)
                        return self.welcome_user(id, question_dict[keys[1]])
                    else:
                        with open(path, mode='r+') as f:
                            state_dict = json.load(f)
                        state = state_dict.get('state')

                        # CANCEL command logic
                        if text.lower() == 'cancel':
                            os.remove(path)
                            return self.send_goodbye(id)

                        # Welcome message validation
                        if state == 'wlcm_msg':
                            if text.lower() not in ['yes', 'no']:
                                err_msg = "Please reply with Yes or No\n\n" + \
                                    question_dict[keys[1]]
                                return self.send_message(id, err_msg)
                            elif text.lower() == 'no':
                                os.remove(path)
                                return self.send_goodbye(id)

                        try:
                            index_of_key = keys.index(state)
                        except ValueError:
                            if state == 'confirm_registration':
                                # Validation to confirm Registration
                                if text.lower() in ['yes', 'no']:
                                    if text.lower() == 'yes':
                                        random_str = get_random_string(8)
                                        os.rename(path, path.replace(
                                            'ongoing.json', 'completed_' + random_str + '.json'))
                                        return self.send_confirmation(id)
                                    elif text.lower() == 'no':
                                        os.remove(path)
                                        return self.send_goodbye(id)
                                else:
                                    return self.confirm_reservation(id, "Please respond by *Yes* or *No*\n\n")

                        # Validation on date format
                        if state == 'date_of_booking':
                            text = text.split('-')
                            try:
                                if len(text) != 3 or int(text[0]) > 28 or int(text[0]) < 1 or int(text[1]) > 12 or int(text[1]) < 1 or int(text[2]) < 2020:
                                    raise ValueError
                            except:
                                err_msg = 'Please enter a Valid date in the given format\n\n' + \
                                    question_dict[keys[index_of_key]]
                                return self.send_message(id, err_msg)
                            finally:
                                text = '-'.join(text)

                        # Validation on time format
                        if state == 'eta':
                            try:
                                text = text.split(':')
                                print(text)
                                if len(text) != 2 or int(text[0]) < 4 or int(text[0]) > 10 or int(text[1]) < 0 or int(text[1]) > 59:
                                    raise ValueError
                            except:
                                err_msg = 'Please enter a Valid time in the given format\n\n' + \
                                    question_dict[keys[index_of_key]]
                                return self.send_message(id, err_msg)
                            finally:
                                text = ':'.join(text)

                        # Validation on phone Number and Name
                        if state == 'full_name_and_enter_phn_number':
                            try:
                                text = text.split('\n')
                                int(text[1])
                                regex = re.compile(r'^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$')
                                if not re.match(regex, text[1]):
                                    raise ValueError
                            except ValueError:
                                err_msg = 'Entered phone number was not valid\n\n' + \
                                    question_dict[keys[index_of_key]]
                                return self.send_message(id, err_msg)
                            except:
                                err_msg = 'Entered information was not in valid format\n\n' + \
                                    question_dict[keys[index_of_key]]
                                return self.send_message(id, err_msg)

                        # Validation for people count
                        if state == 'ppl_count':
                            try:
                                if int(text) not in range(1, 11):
                                    raise ValueError
                            except ValueError:
                                err_msg = 'Please make a choice between 1 to 10\n\n' + \
                                    question_dict[keys[index_of_key]]
                                return self.send_message(id, err_msg)

                        if state == 'full_name_and_enter_phn_number':
                            state_dict[state] = text

                        # Validation on Restraunt choice
                        elif state == 'rstrnt_choice':
                            try:
                                if int(text) not in range(1, 4):
                                    raise ValueError
                            except ValueError:
                                err_msg = 'Please select a valid choice\n\n' + \
                                    question_dict[keys[index_of_key]]
                                return self.send_message(id, err_msg)
                            if text == '1':
                                state_dict[state] = 'Geneva Palace'
                            elif text == '2':
                                state_dict[state] = 'Gopal Restaurant'
                            elif text == '3':
                                state_dict[state] = 'Haveli'

                        else:
                            state_dict[state] = text
                        if index_of_key < len(keys)-1:
                            state_dict['state'] = keys[index_of_key + 1]
                            with open(path, mode='r+') as f:
                                json.dump(state_dict, f)
                            return self.ask_next_question(id, question_dict[keys[index_of_key + 1]])
                        else:
                            state = 'confirm_registration'
                            state_dict['state'] = state
                            with open(path, mode='r+') as f:
                                json.dump(state_dict, f)
                            return self.confirm_reservation(id, '')
                else:
                    return 'No Command'


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
