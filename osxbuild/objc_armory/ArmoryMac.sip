// SIP definition for the Mac dock icon handler code.
// See http://pyqt.sourceforge.net/Docs/sip4/directives.html for more info.

%Copying
Copyright (c) 2011-2014 The Bitcoin developers
Distributed under the MIT/X11 software license. See LICENSE or
http://www.opensource.org/licenses/mit-license.php for more information.

################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
%End

%Module(name=ArmoryMac)

%Import QtCore/QtCoremod.sip
%Import QtGui/QtGuimod.sip

class DockIconClickEventHandler;

// SIP can't handle C++ strings right now. Use QStrings if you can, but code at
// http://www.riverbankcomputing.com/pipermail/pyqt/2011-July/030115.html
// is avaialble if you MUST use C++ strings.

class MacDockIconHandler : public QObject {
%TypeHeaderCode
#include <ArmoryMac.h>
%End

public:
    ~MacDockIconHandler();

    QMenu *dockMenu();
    void setIcon(const QIcon &icon);
    void setMainWindow(QMainWindow *window /KeepReference/ );
    static MacDockIconHandler *instance();

    void handleDockIconClickEvent();

signals:
    void dockIconClicked();

private:
    MacDockIconHandler();
};

class MacNotificationHandler : QObject {
%TypeHeaderCode
#include <ArmoryMac.h>
%End

public:
    // SIP doesn't seem to like enums unless they're part of a class.
	enum notifType
    {
        None,
        Growl12,
        Growl13,
        BuiltIn
    };

    void showNotification(const QString &title, const QString &text);

    void sendAppleScript(const QString &script);

    bool hasUserNotificationCenterSupport();
    MacNotificationHandler::notifType hasGrowl();
    void notifyGrowl(const QString &title, const QString &text, const QIcon &icon);
    static MacNotificationHandler *instance();
}; // class

class MacUtils : QObject {
%TypeHeaderCode
#include <ArmoryMac.h>
%End

public:
    QString openFile();
    static MacUtils* instance();
};
