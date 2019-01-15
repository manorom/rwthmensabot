#!/usr/bin/env python3
import os
import click
from dotenv import load_dotenv, find_dotenv
from telegram import Bot

config_remote = False

def load_env_config():
    token = None
    webhook_path = None
    if config_remote:
        token = os.environ['TELEGRAM_REMOTE_TOKEN']
        webhook_path = os.environ.get('TELEGRAM_REMOTE_WEBHOOK_PATH')
    else:
        token = os.environ['TELEGRAM_TOKEN']
        webhook_path = os.environ.get('TELEGRAM_WEBHOOK_PATH')
    return token, webhook_path

@click.group()
@click.option('--remote', is_flag=True, default=False)
def main(remote):
    load_dotenv(find_dotenv())
    global config_remote
    config_remote = remote


@main.command()
def set():
    token, webhook_path = load_env_config()
    bot = Bot(token)
    print(bot.set_webhook(webhook_path))

@main.command()
def clear():
    token, _ = load_env_config()
    bot = Bot(token)
    print(bot.delete_webhook())

if __name__ == '__main__':
    main()
