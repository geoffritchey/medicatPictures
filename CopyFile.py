import os
import pathlib
from PIL import Image
import cv2
import ftplib
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

send = False
max_modified_time = 0

properties = dict()


def storbinary(ftp, cmd, fp, blocksize=8192, callback=None, rest=None):
    ftp.voidcmd('TYPE I')
    with ftp.transfercmd(cmd, rest) as conn:
        while 1:
            buf = fp.read(blocksize)
            if not buf: break
            conn.sendall(buf)
            if callback: callback(buf)
        if isinstance(conn, ssl.SSLSocket):
            pass
    return ftp.voidresp()


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

    dict_numbers = dict()
    for child in result.get("value"):
        all_id_numbers.add(child["Student"]["StudentNumber"])
        dict_numbers[child["Student"]["StudentNumber"]] = child["Student"]["Id"]

    return all_id_numbers, dict_numbers


if __name__ == '__main__':

    upload_files, mappings = get_current_students()

    f = open("mappings.txt", "w")
    for p in pathlib.Path('//lcuops/images$').glob("*.jpg"):
        if p.is_file():
            if p.stem in upload_files:
                print("found: ", p)
                image = cv2.imread(str(p))
                resize = cv2.resize(image, (63, 73))
                cv2.imwrite("./resized/" + p.name, resize)
                other_id = p.stem
                patient_control_id = mappings[other_id]
                print(f"{patient_control_id if patient_control_id is not None else ''}"
                      , f"{other_id[:20] if other_id is not None else ''}"
                      , sep="|", file=f)
            else:
                print("not found: ", p)
    f.close

'''
Pictures were manually uploaded.  An automated upload has not been written yet.

The Automatic upload below is a clone of nexus CopyPicture, which will need modifications for medicat

    if send:
        if len(upload_files) > 0:
            ftp = ftplib.FTP_TLS(build.sftp_host)
            ftp.login(build.sftp_user, build.sftp_password)
            ftp.prot_p()
            ftp.cwd("/Production/StudentPicureImport")
            print("LIST CWD = ", ftp.pwd())
            print(ftp.retrlines("LIST"))
            for filename in upload_files:
                command = 'STOR ' + filename.name
                print(command, str(filename))
                print('uploading ' + filename.name)
                storbinary(ftp, 'STOR ' + filename.name, open(str(filename), 'rb'))
                print('uploading done ' + filename.name)
            print("LIST CWD = ", ftp.pwd())
            print(ftp.retrlines("LIST"))
            ftp.close()
'''