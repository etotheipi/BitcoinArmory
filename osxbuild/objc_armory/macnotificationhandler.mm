// Copyright (c) 2011-2014 The Bitcoin Core developers
// Distributed under the MIT/X11 software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

////////////////////////////////////////////////////////////////////////////////
//
// Copyright (C) 2011-2014, Armory Technologies, Inc.
// Distributed under the GNU Affero General Public License (AGPL v3)
// See LICENSE or http://www.gnu.org/licenses/agpl.html
//
////////////////////////////////////////////////////////////////////////////////

#include "ArmoryMac.h"

#undef slots
#include <Cocoa/Cocoa.h>
#include <QApplication>
#include <QStyle>
#include <QTemporaryFile>
#include <QBuffer> // TO DO
#include <QImageWriter>


void MacNotificationHandler::showNotification(const QString &title, const QString &text)
{
    // check if users OS has support for NSUserNotification
    if(this->hasUserNotificationCenterSupport()) {
        // okay, seems like 10.8+
        QByteArray utf8 = title.toUtf8();
        char* cString = (char *)utf8.constData();
        NSString *titleMac = [[NSString alloc] initWithUTF8String:cString];

        utf8 = text.toUtf8();
        cString = (char *)utf8.constData();
        NSString *textMac = [[NSString alloc] initWithUTF8String:cString];

        // do everything weak linked (because we will keep <10.8 compatibility)
        id userNotification = [[NSClassFromString(@"NSUserNotification") alloc] init];
        [userNotification performSelector:@selector(setTitle:) withObject:titleMac];
        [userNotification performSelector:@selector(setInformativeText:) withObject:textMac];

        id notificationCenterInstance = [NSClassFromString(@"NSUserNotificationCenter") performSelector:@selector(defaultUserNotificationCenter)];
        [notificationCenterInstance performSelector:@selector(deliverNotification:) withObject:userNotification];

        [titleMac release];
        [textMac release];
        [userNotification release];
    }
}

// sendAppleScript just take a QString and executes it as apple script
void MacNotificationHandler::sendAppleScript(const QString &script)
{
    QByteArray utf8 = script.toUtf8();
    char* cString = (char *)utf8.constData();
    NSString *scriptApple = [[NSString alloc] initWithUTF8String:cString];

    NSAppleScript *as = [[NSAppleScript alloc] initWithSource:scriptApple];
    NSDictionary *err = nil;
    [as executeAndReturnError:&err];
    [as release];
    [scriptApple release];
}

bool MacNotificationHandler::hasUserNotificationCenterSupport(void)
{
    Class possibleClass = NSClassFromString(@"NSUserNotificationCenter");

    // check if users OS has support for NSUserNotification
    if(possibleClass!=nil) {
        return true;
    }
    return false;
}


// Borrowed from Bitcoin-Qt's Notificator::Notificator()  (src/notificator.cpp)
MacNotificationHandler::notifType MacNotificationHandler::hasGrowl(void)
{
    notifType retVal = None;

    // Check if Growl is installed (based on Qt's tray icon implementation)
    CFURLRef cfurl;
    OSStatus status = LSGetApplicationForInfo(kLSUnknownType,
                                              kLSUnknownCreator,
                                              CFSTR("growlTicket"),
                                              kLSRolesAll,
                                              0,
                                              &cfurl);
    if(status != kLSApplicationNotFoundErr) {
        CFBundleRef bundle = CFBundleCreate(0, cfurl);
        if(CFStringCompare(CFBundleGetIdentifier(bundle),
                           CFSTR("com.Growl.GrowlHelperApp"),
                           kCFCompareCaseInsensitive | kCFCompareBackwards)
           == kCFCompareEqualTo) {
            if (CFStringHasSuffix(CFURLGetString(cfurl), CFSTR("/Growl.app/"))) {
                retVal = Growl13;
            }
            else {
                retVal = Growl12;
            }
        }
        CFRelease(cfurl);
        CFRelease(bundle);
    }

    return retVal;
}


// Borrowed from Bitcoin-Qt's Notificator::notifyGrowl()  (src/notificator.cpp)
void MacNotificationHandler::notifyGrowl(const QString &title, const QString &text, const QIcon &icon)
{
    const QString script(
        "tell application \"%5\"\n"
        " set the allNotificationsList to {\"Notification\"}\n" // -- Make a list of all the notification types (all)
        " set the enabledNotificationsList to {\"Notification\"}\n" // -- Make a list of the notifications (enabled)
        " register as application \"%1\" all notifications allNotificationsList default notifications enabledNotificationsList\n" // -- Register our script with Growl
        " notify with name \"Notification\" title \"%2\" description \"%3\" application name \"%1\"%4\n" // -- Send a Notification
        "end tell"
    );

    QString notificationApp(QApplication::applicationName());
    if (notificationApp.isEmpty())
        notificationApp = QString("Application");

    QPixmap notificationIconPixmap;
    if (icon.isNull()) { // If no icon specified, set icon based on class
        QStyle::StandardPixmap sicon = QStyle::SP_MessageBoxQuestion;
        sicon = QStyle::SP_MessageBoxInformation;
        notificationIconPixmap = QApplication::style()->standardPixmap(sicon);
    }
    else {
        QSize size = icon.actualSize(QSize(48, 48));
        notificationIconPixmap = icon.pixmap(size);
    }

    QString notificationIcon;
    QTemporaryFile notificationIconFile;
    if (!notificationIconPixmap.isNull() && notificationIconFile.open()) {
        QImageWriter writer(&notificationIconFile, "PNG");
        if (writer.write(notificationIconPixmap.toImage()))
            notificationIcon = QString(" image from location \"file://%1\"").arg(notificationIconFile.fileName());
    }

    QString quotedTitle(title), quotedText(text);
    quotedTitle.replace("\\", "\\\\").replace("\"", "\\");
    quotedText.replace("\\", "\\\\").replace("\"", "\\");
	notifType growlVer = hasGrowl();
    QString growlApp(growlVer == Growl13 ? "Growl" : "GrowlHelperApp");
    sendAppleScript(script.arg(notificationApp, quotedTitle, quotedText, notificationIcon, growlApp));
}


MacNotificationHandler *MacNotificationHandler::instance()
{
    static MacNotificationHandler *s_instance = NULL;
    if (!s_instance)
        s_instance = new MacNotificationHandler();
    return s_instance;
}
