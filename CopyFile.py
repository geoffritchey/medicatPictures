import os
import pathlib
from PIL import Image
import cv2
import pysftp
import build
import time
import json
import datetime
import ssl
import logging
import Util

logging.basicConfig(format='%(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

send = True
max_modified_time = 0

properties = dict()


def get_current_students(session=Util.authenticated_session, today=datetime.datetime.now()):
    log.debug(today)
    all_id_numbers = set()
    '''
    Find current list of students
    '''
    students_uri = "{0}ds/campusnexus/StudentCourses?$count=true" \
                   "&$expand=Student($expand=Gender($select=Code))" \
                   ",Student($expand=EmploymentStatus)" \
                   ",Student($expand=College)" \
                   ",Student($select=Id,Ssn,StudentNumber,LastName,FirstName,MiddleName,DateOfBirth,StreetAddress" \
                   ",StreetAddress2,City,State,PostalCode,WorkPhoneNumber,MobilePhoneNumber,PhoneNumber,EmailAddress," \
                   "DateOfBirth,MaritalStatusId,NickName)" \
                   "&$filter=Term/EndDate ge {1} and Term/StartDate le {2} " \
                   "&$select=Status,Student,StudentEnrollmentPeriodId" \
                   "&$orderby=Student/StudentNumber" \
                   "&$apply=groupby((Student/StudentNumber))" \
                   "".format(Util.root_uri, today.strftime("%Y-%m-%d"), (today + datetime.timedelta(weeks=4)).strftime("%Y-%m-%d"))
    print("url = ", students_uri)

    r = session.get(students_uri)
    r.raise_for_status()
    log.debug(students_uri)
    # log.debug(r.text)
    result = json.loads(r.text)
    log.debug(result)

    # start period list as a set to get distinct values
    # then convert it to a list for easy of use

    id_to_picture_file_mapping = dict()
    for child in result.get("value"):
        all_id_numbers.add(child["Student"]["StudentNumber"])
        id_to_picture_file_mapping[child["Student"]["StudentNumber"]] = child["Student"]["Id"]

    return all_id_numbers, id_to_picture_file_mapping


if __name__ == '__main__':
    new_files_to_upload = []
    try:
        with open('properties.txt') as f:
            properties = json.load(f)
    except json.JSONDecodeError as err:
        print(err)

    try:
        str_last_modify = properties['last_modified']
    except:
        str_last_modify = "1900-01-01 00:00:00"

    print("last_modify = ", str_last_modify)
    last_modify_time = datetime.datetime.strptime(str_last_modify, "%Y-%m-%d %H:%M:%S").timestamp()

    upload_files, mappings = get_current_students()

    f = open("mappings.txt", "w")
    for p in pathlib.Path('//lcuops/images$').glob("*.jpg"):
        if p.is_file():
            if p.stem in upload_files:
                other_id = p.stem
                patient_control_id = mappings[other_id]
                print(f"{patient_control_id if patient_control_id is not None else ''}"
                      , f"{other_id[:20] if other_id is not None else ''}"
                      , sep="|", file=f)
                modified = int(os.path.getmtime(p))
                if modified > last_modify_time:
                    print("found: ", p)
                    image = cv2.imread(str(p))
                    resize = cv2.resize(image, (63, 73))
                    cv2.imwrite("./resized/" + p.name, resize)
                    new_files_to_upload.append(p.name)
                if modified > max_modified_time:
                    max_modified_time = modified
    f.close

    if send:
        if len(new_files_to_upload) > 0:
            os.chdir("resized")
            ftp = pysftp.Connection(build.sftp_host, username=build.sftp_username, password=build.sftp_password)
            ftp.cwd("1376Photos")
            print("LIST CWD = ", ftp.pwd)
            for filename in new_files_to_upload:
                print('uploading ' + filename)
                ftp.put(filename)
                print('uploading done ' + filename)
            print("LIST CWD = ", ftp.pwd)
            ftp.close()

            time = datetime.datetime.strptime(time.ctime(max_modified_time), "%a %b %d %H:%M:%S %Y").strftime(
                "%Y-%m-%d %H:%M:%S")
            print(time)
            properties['last_modified'] = time
            print(properties)
            os.chdir("..")
            with open('properties.txt', 'w+') as f:
                json.dump(properties, f)
