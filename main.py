import os
import json
from random import shuffle, randint
from uuid import uuid1
from dotenv import load_dotenv
from vk_api import VkApi
from vk_api.exceptions import BadPassword

from utils import manage_empty_q, read_file, write_to_file
from constants import MODES, LAST_NAMES


def auth(login: str, password: str):
    session = VkApi(login, password)
    try:
        session.auth()
    except BadPassword:
        return None
    return session.get_api()


def get_poll(vk, poll_id: int):
    response = vk.polls.getById(poll_id=poll_id)
    if not response:
        return print(f'Failed to get poll {poll_id} info')
    if not response.get('answers'):
        return print(f'Poll {poll_id} doesn\'t have any questions')
    q = response.get('question')
    if q:
        print(q)
    answers = dict()
    for i, ans in enumerate(response['answers'], 1):
        ans_id = ans.get('id')
        if not ans_id:
            print(f'{i}. Failed to get ans_id')
            continue
        ans_text = ans.get('text')
        if input(f'{i}. {ans_text} ({ans_id}) (0/1): ').lower() == '1':
            answers[str(ans_id)] = ans_text
    if not answers:
        return print('There are no answers to be checked')
    voters = vk.polls.getVoters(poll_id=poll_id, answer_ids=','.join(answers.keys()),
                                fields='last_name', lang='ru')
    with open('voters.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(voters, indent=4, ensure_ascii=False))
    answers_output = dict()
    for i, ans in enumerate(voters):
        ans_id = str(ans.get('answer_id'))
        if not ans_id:
            print('Failed to get answer_id')
            continue
        users_d = ans.get('users')
        if not users_d:
            print(f'Users information is missed for answer_id {ans_id}')
            continue
        users_count = users_d.get('count')
        ans_text = answers[ans_id] if answers[ans_id] else str(i)
        print(f'{ans_text}: {users_count} votes')
        items = users_d.get('items')
        if not items and users_count:
            print(f'Items are missed for answer_id {ans_id}')
            continue
        answers_output[ans_id] = {'text': ans_text, 'voters': []}
        for j, item in enumerate(items, 1):
            surname = item.get('last_name')
            if not surname:
                print(f'Surname missed on item #{j}')
                continue
            if surname in answers_output:
                continue
            answers_output[ans_id]['voters'].append(surname if surname not in LAST_NAMES
                                                    else LAST_NAMES[surname])
    return q, answers_output


def refresh(q: str, answers: dict):
    q = manage_empty_q(q)
    for ans_id in answers:
        voters = answers[ans_id]['voters']
        shuffle(voters)
        write_to_file(os.path.join(q, f'{answers[ans_id]["text"]}.txt'), voters)


def add(q: str, answers: dict):
    if not q:
        raise Exception('q cannot be empty')
    for ans_id in answers:
        ans_text = answers[ans_id]['text']
        new_voters = answers[ans_id]['voters']
        voters = read_file(os.path.join(q, f'{ans_text}.txt'))
        dif = set(new_voters).difference(voters)
        while dif:
            voter = dif.pop()
            voters.insert(randint(0, len(voters)), voter)
        write_to_file(os.path.join(q, f'{ans_text}.txt'), voters)


def main():
    login = os.getenv('login')
    if not login:
        return print('Login should be specified in .env')
    password = os.getenv('password')
    if not password:
        return print('Password should be specified in .env')
    try:
        poll_id = os.getenv('poll_id')
        if not poll_id:
            return print('poll_id should be specified in .env')
        poll_id = int(poll_id)
    except ValueError:
        return print('Invalid poll_id was specified in .env')
    while True:
        try:
            mode_idx = int(input('Choose a mode: ' + '\n' + 
                            '\n'.join([f'{i + 1} – {MODES[i]}' 
                                       for i in range(len(MODES))]) + '\n'))
            assert 1 <= mode_idx <= len(MODES)
        except (ValueError, AssertionError):
            print(f'A natural number from 1 to {len(MODES)}')
        else:
            break
    vk = auth(login, password)
    if not vk:
        return print('Wrong login or password were given')
    q, answers = get_poll(vk, poll_id)
    if mode_idx == 1:
        refresh(q, answers)
    elif mode_idx == 2:
        add(q, answers)


if __name__ == '__main__':
    load_dotenv()
    main()