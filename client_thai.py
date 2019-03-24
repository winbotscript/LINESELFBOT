from linepy import LINE as CLIENT
from linepy import OEPoll
from datetime import datetime
from akad.ttypes import LiffViewRequest, LiffContext, LiffChatContext, Operation, Message
import json
import codecs
import time
import sys
import os
import requests

clientFileLocation = 'settings.json'
clientSettingsLoad = codecs.open(clientFileLocation, 'r', 'utf-8')
clientSettings = json.load(clientSettingsLoad)
if "startTime" not in clientSettings:
    clientSettings["startTime"] = time.time()
if "mimic" not in clientSettings:
    clientSettings["mimic"] = {}
if "spamGroupProtect" not in clientSettings:
    clientSettings["spamGroupProtect"] = {}
clientStartTime = clientSettings["startTime"]

try:
    client = CLIENT(clientSettings["authToken"], appName=clientSettings["appName"], showQr=True)
except:
    client = CLIENT(appName=clientSettings["appName"], showQr=True)

clientMid = client.profile.mid
clientPoll = OEPoll(client)
clientErrorOrNewPatch = []

listHelpMessage = {
    "รายละเอียดบัญชี": "ftitle",
	"ชื่อผู้ใช้งาน: {dp}": "dtail",
	"เวลาทำงาน: {rt}": "dtail",
	"ไอดี: {mid}": "dtail",
    "คำสั่งทั่วไป": "title",
    "โปรไฟล์": "profile (@)",
    "ข้อมูลติดต่อ": "contact (@)",
    "ดู Mid ผู้ใช้": "mid (@)",
	"ทดสอบความเร็วในการทำงาน": "optest",
	"ทดสอบความเร็วในการรับข้อมูล": "speed",
	"ดูเวลาทำงาน": "runtime",
	"ดูบัญชีที่อ่านข้อความ":"reader",
	"แท็กสมาชิกทั้งหมด":"tagall",
	"คำสั่งพิเศษ": "title",
	"แชทบอท": "chatbot",
	"บัญชี": "title",
	"บังคับเริ่มระบบใหม่": "freboot",
	"เริ่มระบบใหม่": "reboot",
	"ออกจากระบบ": "logout"
}
helpMessageLine = "-"*10
# THIS IS ERROR #helpMessage = ["\n- {}{} {}".format(clientSettings["prefix"], cmd, listHelpMessage[cmd]) if cmd not in ["fTitle","title"] else "{l} {c} {l}".format(c=listHelpMessage[cmd], l=helpMessageLine) if cmd == "fTitle" else "\n\n{l} {c} {l}".format(c=listHelpMessage[cmd], l=helpMessageLine) for cmd in listHelpMessage]
helpMessage = []
for x in listHelpMessage:
    if listHelpMessage[x] not in ["ftitle","title","dtail"]:
        helpMessage.append("\n- {pre}{cmd} {des}".format(pre=clientSettings['prefix'], des=x, cmd=listHelpMessage[x]))
    elif listHelpMessage[x] not in ["dtail"]:
        lines = "\n\n{l} {title} {l}"
        if listHelpMessage[x] == "ftitle":
            lines = "{l} {title} {l}"
        helpMessage.append(lines.format(l=helpMessageLine, title=x))
    else:
        helpMessage.append("\n{cmd}".format(cmd=x))
clientHelpMessage = "".join(helpMessage)

if "reader" not in clientSettings:
    clientSettings["reader"] = {}
    clientSettings["reader"]["readRom"] = {}

def log(text):
    global client
    print("[%s] [%s] : %s" % (str(datetime.now()), client.profile.displayName, text))

def getProfile():
    global client
    client.profile = client.getProfile()
    if "profile" not in clientSettings:
        clientSettings["profile"] = {}
    clientSettings["profile"]["displayName"] = client.profile.displayName
    clientSettings["profile"]["statusMessage"] = client.profile.statusMessage
    clientSettings["profile"]["pictureStatus"] = client.profile.pictureStatus
    return client.profile

def commandMidContact(to, mid, cmd):
    if cmd in ["mid","contact"]:
        if cmd == "mid":
            return client.sendMessage(to, mid)
        if cmd == "contact":
            return client.sendContact(to, mid)
    return
	
def commandAddOrDel(to, mid, cmd):
    global clientSettings
    if cmd in ["on","off"]:
        if cmd == "on":
            text = 'เพิ่ม {} เข้ารายชื่อที่ลอกเลียนแบบแล้ว'
            if mid not in clientSettings['mimic'][to]:
                clientSettings['mimic'][to][mid] = True
            else:
                text = '{} อยู่ในบัญชีที่ลอกเลียนแบบอยู่แล้ว'
            return client.sendMessage(to, text.format(client.getContact(mid).displayName))
        if cmd == "off":
            text = 'ลบ {} ออกจากรายชื่อที่ลอกเลียนแบบแล้ว'
            if mid in clientSettings['mimic'][to]:
                del clientSettings['mimic'][to][mid]
            else:
                text = '{} ไม่ได้อยู่ในบัญชีที่ลอกเลียนแบบ'
            return client.sendMessage(to, text.format(client.getContact(mid).displayName))
    return

def getCommand(text):
    global clientSettings
    if text.startswith(clientSettings["prefix"]):
        return text.split(" ")[0][1:].lower()
    return "False"

def oneOnList(text):
    global clientSettings
    if text.startswith(clientSettings["prefix"]):
        if len(text.split(" ")) == 1:
            return True
    return False

def settingsCommand(text):
    setTo = None if len(text.split(" ")) != 2 else 'on' if text.split(" ")[1] == 'on' else 'off' if text.split(" ")[1] == 'off' else None
    return setTo
	
def settingsCommand2(text):
    setTo = text.split(":")
    if len(setTo) == 1: return None
    setTo = setTo[1]
    if setTo == "add":
        return "on"
    elif setTo == "del":
        return "off"
    return None
	
def saveSettings():
    global clientSettings
    try:
        f=codecs.open(clientFileLocation,'w','utf-8')
        json.dump(clientSettings, f, sort_keys=True, indent=4, ensure_ascii=False)
    except Exception as e:
        log(str(e))
	
def sendFlex(to, data):
    view = client.issueLiffView(LiffViewRequest("1616062718-gRzkqKmm",LiffContext(chat=LiffChatContext(chatMid=to))))
    headers = {'content-type': 'application/json', "Authorization": "Bearer %s" % view.accessToken, "X-Requested-With": "jp.naver.line.android", "Connection": "keep-alive"}
    data = {"messages": [data]}
    post = requests.post("https://api.line.me/message/v3/share", headers=headers,data=json.dumps(data))
	
def mentionMembers(to, mids=[], result=''):
    parsed_len = len(mids)//20+1
    mention = '@freeclient\n'
    no = 0
    for point in range(parsed_len):
        mentionees = []
        for mid in mids[point*20:(point+1)*20]:
            no += 1
            result += '%i. %s' % (no, mention)
            slen = len(result) - 12
            elen = len(result) + 3
            mentionees.append({'S': str(slen), 'E': str(elen - 4), 'M': mid})
        if result:
            if result.endswith('\n'): result = result[:-1]
            client.sendMessage(to, result, {'MENTION': json.dumps({'MENTIONEES': mentionees})}, 0)
        result = ''
	
def getRuntime():
    totalTime = time.time() - clientStartTime
    mins, secs = divmod(totalTime, 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)
    resTime = ""
    if days != 00:
         resTime += "%2d วัน " % (days)
    if hours != 00:
        resTime += "%2d ชั่วโมง " % (hours)
    if mins != 00:
        resTime += "%2d นาที " % (mins)
    resTime += "%2d วินาที" % (secs)
    return resTime
	
OPTEST = {}
MimicTEMP = []
	
def execute(op):
    global clientSettings
    global OPTEST
    global clientErrorOrNewPath
    if op.type == 1:
        return getProfile()
    if op.type == 13:
        client.acceptGroupInvitation(op.param1)
        group = client.getGroup(op.param1)
        if group.name in clientSettings["spamGroupProtect"]:
            for x in clientSettings["spamGroupProtect"]:
                if x == group.name:
                    client.leaveGroup(clientSettings["spamGroupProtect"][x])
            return client.leaveGroup(group.id)
        clientSettings["spamGroupProtect"][group.name] = group.id
    if op.type == 22:
        client.leaveRoom(op.param1)
    if op.type == 25:
        msg = op.message
        text = msg.text
        to = msg.to
        if text is None:
            return
        if msg.id in MimicTEMP:
            MimicTEMP.remove(msg.id)
            return
        if msg.id in OPTEST:
            totalTime = time.time() - OPTEST[msg.id]
            del OPTEST[msg.id]
            client.sendMessage(to, "Pong! ({} ms)\n{} วินาที".format(str(totalTime*1000).split(".")[0], totalTime))
        cmd = getCommand(text)
        ononlist = oneOnList(text)
        if cmd == "False":
            clientSettings["reader"]["readRom"][to] = {}
            return
        fullCmd = (clientSettings["prefix"]+cmd)
        if cmd == "help" and ononlist:
            return client.sendMessage(to, clientHelpMessage.format(dp=client.profile.displayName,mid=client.profile.mid[:len(client.profile.mid)-20]+"*"*7, rt=getRuntime()))
        if cmd == "optest" and ononlist:
            for x in range(5):
                OPTEST[client.sendMessage(to, ".").id] = time.time()
        if cmd in ["mimic:add","mimic:del","mimic"]:
            if to not in clientSettings['mimic']:
                clientSettings['mimic'][to] = {}
            if settingsCommand2(cmd) == None and cmd == "mimic":
                midsList = [client.getContact(mid).displayName for mid in clientSettings['mimic'][to]]
                if midsList == []:
                    return client.sendMessage(to, 'ไม่มีรายชื่อที่ลอกเลียนแบบ')
                text = "รายชื่อบัญชีที่เลียนแบบ:\n"
                for x in text: text+="\n- {}".format(x)
                return client.sendMessage(to, text)
            cmd = settingsCommand2(cmd)
            if cmd is not None:
                midsList = []
                if "MENTION" in msg.contentMetadata:
                    key = eval(msg.contentMetadata["MENTION"])
                    for x in [i["M"] for i in key["MENTIONEES"]]:
                        midsList.append(x)
                for mid in midsList:
                    if len(mid) == len(clientMid):
                        commandAddOrDel(to, mid, cmd)
                return
        if cmd == "runtime" and ononlist:
            client.sendMessage(to, getRuntime())
        if cmd == "speed" and ononlist:
            startTime = time.time()
            pingMessage = getProfile()
            totalTime = time.time() - startTime
            client.sendMessage(to, "Pong! ({} ms)\n{} วินาที".format(str(totalTime*1000).split(".")[0], totalTime))
        if cmd in ["contact","mid"]:
            if len(msg.text.split(" ")) == 1:
                return commandMidContact(to, clientMid, cmd)
            else:
                if msg.text.split(" ")[1] == "@":
                    if msg.toType == 0:
                        commandMidContact(to, to, cmd)
            midsList = []
            if "MENTION" in msg.contentMetadata:
                key = eval(msg.contentMetadata["MENTION"])
                for x in [i["M"] for i in key["MENTIONEES"]]:
                    midsList.append(x)
            for x in msg.text.split(" "):
                if len(x) == len(clientMid):
                    midsList.append(x)
            if fullCmd in midsList:
                midsList.remove(fullCmd)
            for mid in midsList:
                if len(mid) == len(clientMid):
                    commandMidContact(to, mid, cmd)
            return
        if cmd == "reader" and ononlist:
            if to not in clientSettings["reader"]["readRom"]:
                clientSettings["reader"]["readRom"][to] = {}
            readerMids = [i for i in clientSettings["reader"]["readRom"][to]]
            if readerMids == []:
                return client.sendMessage(to, 'ไม่มีบัญชีที่อ่านข้อความ')
            return mentionMembers(to, readerMids, 'บัญชีที่อ่านข้อความ:\n')
        if cmd == 'tagall' and ononlist:
            membersMidsList = []
            if msg.toType == 1:
                room = client.getCompactRoom(to)
                membersMidsList = [member.mid for member in room.members]
            elif msg.toType == 2:
                group = client.getCompactGroup(to)
                membersMidsList = [member.mid for member in group.members]
            else:
                return membersMidsList.append(to)
            if membersMidsList:
                if clientMid in membersMidsList: membersMidsList.remove(clientMid)
                if membersMidsList == []:
                    return client.sendMessage(to, "ไม่มีสมาชิกในกลุ่มหรือห้องแชท")
                return mentionMembers(to, membersMidsList)
        if cmd == "profile" and ononlist:
            profileList = []
            if len(msg.text.split(" ")) == 1:
                profile = getProfile()
                profileList = [profile]
            else:
                if msg.text.split(" ")[1] == "@":
                    if msg.toType == 0:
                        profileList.append(client.getContact(to))
            if "MENTION" in msg.contentMetadata:
                key = eval(msg.contentMetadata["MENTION"])
                for x in [i["M"] for i in key["MENTIONEES"]]:
                    profileList.append(client.getContact(x))
            if profileList == []:
                for x in msg.text.split(" "):
                    if len(x) == len(clientMid):
                        profileList.append(client.getContact(x))
            if fullCmd in profileList: profileList.remove(fullCmd)
            for profile in profileList:
                if len(profile.mid) == len(clientMid):
                    if profile.pictureStatus: profilePicURL = "https://profile.line-scdn.net/" + profile.pictureStatus
                    else: profilePicURL = "https://pasunx.tk/ww.jpg"
                    if profile.displayName: displayName = profile.displayName
                    else: displayName = "Unknow"
                    statusMessage = profile.statusMessage if profile.statusMessage != "" else " "
                    profileCoverURL = client.getProfileCoverURL()
                    statusMessageContents = {"type": "text","text": statusMessage,"wrap": True,"size": "xs","color": "#000000","weight": "bold","align": "center","flex": 1}
                    flexContents = {"type": "bubble","hero": {"type": "image","url": profileCoverURL,"size": "full","aspectRatio": "16:9","aspectMode": "cover","action": {"type": "uri","uri": "https://linecorp.com"}},"body": {"type": "box","layout": "vertical","spacing": "md","contents": [{"type": "box","layout": "vertical","spacing": "sm","contents": [{"type": "image","url": profilePicURL,"aspectMode": "cover","size": "xl"},{"type": "text","text": displayName,"wrap": True,"size": "lg","color": "#000000","weight": "bold","align": "center","flex": 0},statusMessageContents]}]}}
                    data = {"type": "flex", "altText": displayName, "contents":flexContents}
                    sendFlex(to, data)
            return
        if cmd == "error" and ononlist:
            text = "ข้อผิดพลาดที่บันทึก:"
            if clientErrorOrNewPatch == []:
                return client.sendMessage(to, "ไม่มีข้อผิดพลาดหรือไม่พบข้อผิดพลาดที่ถูกบันทึก")
            for e in clientErrorOrNewPatch:
                text+="\n- {}".format(e)
            text+="\n\nรายงานข้อผิดพลาดได้ที่:\nline://ti/p/~{spcontact}"
            client.sendMessage(to, text)
        if cmd == "chatbot":
            return client.sendMessage(to, "กรุณาตั้งค่าข้อมูลส่วนตัว\n'{pre}chatbot settings'".format(pre=clientSettings["prefix"]))
        if cmd == "reboot" and ononlist:
            if clientErrorOrNewPatch == []:
                return client.sendMessage(to, "ไม่พบข้อผิดพลาดหรือแพทช์ใหม่")
            clientSettings["rebootTime"] = time.time()
            clientSettings["lastOp"] = str(op)
            saveSettings()
            time.sleep(0.5)
            client.sendMessage(to, "กำลังเริ่มระบบใหม่อีกครั้ง")
            time.sleep(1)
            python = sys.executable
            os.execl(python, python, *sys.argv)
        if cmd == "freboot" and ononlist:
            op.message.text = "{}reboot".format(clientSettings["prefix"])
            clientErrorOrNewPatch.append("Force Reboot")
            client.sendMessage(to, "กรุณารอสักครู่")
            time.sleep(0.5)
            execute(op)
        if cmd == "logout" and ononlist:
            del clientSettings["startTime"]
            clientSettings["lastOp"] = None
            saveSettings()
            time.sleep(1)
            sys.exit()
    if op.type == 26:
        msg = op.message
        to = msg._from if msg.toType == 0 else msg.to
        if to in clientSettings["mimic"]:
            if msg._from in clientSettings["mimic"][to]:
                if msg.contentType == 0:
                    if msg.text is not None:
                        MimicTEMP.append(client.sendMessage(to, msg.text).id)
    if op.type == 55:
        if op.param1 not in clientSettings["reader"]["readRom"]:
            clientSettings["reader"]["readRom"][op.param1] = {}
        if op.param2 not in clientSettings["reader"]["readRom"][op.param1]:
            clientSettings["reader"]["readRom"][op.param1][op.param2] = True
    clientSettings["lastOp"] = None
		
if client.authToken != clientSettings["authToken"]:
    clientSettings["authToken"] = client.authToken
    log("Save new auth token")
    saveSettings()
		
if "lastOp" not in clientSettings:
    clientSettings["lastOp"] = None
if clientSettings["lastOp"] is not None:
    op = eval(clientSettings["lastOp"])
    if op.type == 25:
        if op.message.text == "{}reboot".format(clientSettings["prefix"]):
            rebootMSG = ""
            if "rebootTime" in clientSettings:
                totalTime = str(time.time()-clientSettings["rebootTime"]).split(".")
                totalTime = totalTime[0] + "." + totalTime[1][:2]
                rebootMSG = " - {} วินาที".format(totalTime)
            client.sendMessage(op.message.to, "เริ่มระบบใหม่อีกครั้งเรียบร้อยแล้ว{}".format(rebootMSG))
            clientSettings["lastOp"] = None
    else:
        execute(op)
		
while True:
    ops = clientPoll.singleTrace(count=100)
    if ops != None:
        for op in ops:
            try:
                clientSettings["lastOp"] = str(op)
                execute(op)
            except Exception as e:
                clientErrorOrNewPatch.append(e)
                client.sendMessage(eval(clientSettings["lastOp"]).message.to, "พบข้อผิดพลาดพิมพ์ '{x}error' เพื่อดูข้อผิดพลาด\nหรือพิมพ์ '{x}reboot' เพื่อเริ่มระบบใหม่อีกครั้ง".format(x=clientSettings["prefix"]))
                log(str(e))
            clientPoll.setRevision(op.revision)