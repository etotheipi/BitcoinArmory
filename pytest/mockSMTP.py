import smtpd
import asyncore

class CustomSMTPServer(smtpd.SMTPServer):
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        f = open("email.tmp", "w")
        f.write(data)
        f.close()


server = CustomSMTPServer(('127.0.0.1', 1025), None)

asyncore.loop()
