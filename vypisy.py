#!/usr/bin/env python3
'echo' 'Start this program with python'
'exit' '1'

import requests
from configparser import ConfigParser
import datetime
import os.path
import time
from zipfile import ZipFile
from pprint import pprint

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib


CONFIG_FILE = 'tokens.ini'
URI = 'https://www.fio.cz/ib_api/rest/by-id/{token}/{year}/{month_index}/transactions.{format}'
FILENAME = '{year:04d}/{year:04d}-{month:02d}-{name}-{number}.{format}'
SUBJECT = '{subject_template} za {year:04d}/{month:02d}'

def get_archives(config):
    archives = {}
    is_changed,is_complete = False, True

    now = datetime.datetime.now()
    last_month = now - datetime.timedelta(days=now.day+1)

    required_formats = config['config']['formats'].split()
    for file_format in required_formats:
        for section_name in config:
            if not section_name.startswith('account:'):
                continue
            params = dict(
                name=section_name.split(':')[-1],
                token=config[section_name]['token'],
                number=config[section_name]['account'],
                month=last_month.month,
                month_index=last_month.month,
                year=last_month.year,
                format=file_format,
            )
            if 'offset' in config[section_name]:
                offset = int(config[section_name]['offset'])
                params['month_index'] = int(params['month']) - offset
            filename = FILENAME.format(**params)
            archive_name = config[section_name]['archive']
            if not archive_name in archives:
                archives[archive_name] = []
            archives[archive_name].append(filename)
            #
            if os.path.isfile(filename):
                print("INFO : Skipping already downloaded {}".format(filename))
                continue

            print("INFO : Downloading {}".format(filename))
            resp = requests.get(URI.format(**params))
            if resp.status_code == 200:
                with open(filename, 'wb') as f:
                    print("INFO : Saving {}".format(filename))
                    f.write(resp.content)
                    is_changed = True
            elif resp.status_code == 409:
                print("ERROR: 409: We should wait for 30 seconds and retry")
                is_complete = False
            elif resp.status_code == 500:
                print("ERROR: 500: We should wait for one day and retry")
                is_complete = False
            else:
                print("ERROR: Unknown error - got {}".format(resp.status_code))
                raise SystemExit
    #print("Filenames =", archives)
    #
    archive_files = {}
    for archive_name in archives.keys():
        archive_fname = last_month.strftime(f'archive-{archive_name}-%Y-%m.zip')
        archive_files[archive_name] = archive_fname
        with ZipFile(archive_fname, 'w') as archive:
            for filename in archives[archive_name]:
                archive.write(filename, arcname=os.path.basename(filename))

    return archive_files


def send_to_mail(config, archive_files):
    """
    Send Archive files to e-mails

    :param archive_files:
    :return:
    """

    now = datetime.datetime.now()
    last_month = now - datetime.timedelta(days=now.day + 1)

    for archive_name,archive_filename in archive_files.items():
        print(archive_name, archive_filename)

        # skip archive send when mailto: is not present
        if not config.has_section(f'mailto:{archive_name}'):
            print(f"Missing send config for {archive_name}. Sending skipped")
            continue

        mailfrom = config[f'mailto:{archive_name}']['mailfrom']
        mailto = config[f'mailto:{archive_name}']['mailto']
        replyto = config[f'mailto:{archive_name}']['replyto']

        # create Mime object for email
        msg = MIMEMultipart()
        msg['From'] = mailfrom
        msg['To'] = mailto
        msg['Cc'] = replyto
        msg['Reply-To'] = replyto
        subject_template = config[f'mailto:{archive_name}']['subject_txt']
        msg['Subject'] = SUBJECT.format(
                            subject_template=subject_template,
                            month=last_month.month, year=last_month.year)

        # create mail body
        body = config[f'mailto:{archive_name}']['body']
        # with encoding
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        zip_archive = open(archive_filename, 'rb')
        zip_part = MIMEBase('application', 'zip')
        zip_part.set_payload(zip_archive.read())
        encoders.encode_base64(zip_part)
        zip_part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(archive_filename)))
        msg.attach(zip_part)

        # Send the email
        server = smtplib.SMTP(config[f'mailto:{archive_name}']['smtp_server'], 587)
        server.starttls()
        login = config[f'mailto:{archive_name}']['mailfrom']
        password = config[f'mailto:{archive_name}']['mailpassword']
        server.login(login, password)
        server.sendmail(mailfrom, mailto, msg.as_string())
        server.quit()


if __name__ == '__main__':
    config = ConfigParser()
    config.read(CONFIG_FILE)

    archives = get_archives(config)

    send_to_mail(config, archives)
