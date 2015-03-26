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

#include <QMenu>
#include <QWidget>
#include <QtMac>

#undef slots
#include <Cocoa/Cocoa.h>

@interface DockIconClickEventHandler : NSObject
{
    MacDockIconHandler* dockIconHandler;
}

@end

@implementation DockIconClickEventHandler

- (id)initWithDockIconHandler:(MacDockIconHandler *)aDockIconHandler
{
    self = [super init];
    if (self) {
        dockIconHandler = aDockIconHandler;

        [[NSAppleEventManager sharedAppleEventManager]
            setEventHandler:self
                andSelector:@selector(handleDockClickEvent:withReplyEvent:)
              forEventClass:kCoreEventClass
                 andEventID:kAEReopenApplication];
    }
    return self;
}

- (void)handleDockClickEvent:(NSAppleEventDescriptor*)event withReplyEvent:(NSAppleEventDescriptor*)replyEvent
{
    Q_UNUSED(event)
    Q_UNUSED(replyEvent)

    if (dockIconHandler) {
        dockIconHandler->handleDockIconClickEvent();
    }
}

@end

MacDockIconHandler::MacDockIconHandler() : QObject()
{
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];

    this->m_dockIconClickEventHandler = [[DockIconClickEventHandler alloc] initWithDockIconHandler:this];
    this->m_dummyWidget = new QWidget();
    this->m_dockMenu = new QMenu(this->m_dummyWidget);
    this->setMainWindow(NULL);
    this->m_dockMenu->setAsDockMenu();
    [pool release];
}

void MacDockIconHandler::setMainWindow(QMainWindow *window) {
    this->mainWindow = window;
}

MacDockIconHandler::~MacDockIconHandler()
{
    [this->m_dockIconClickEventHandler release];
    delete this->m_dummyWidget;
    this->setMainWindow(NULL);
}

QMenu *MacDockIconHandler::dockMenu()
{
    return this->m_dockMenu;
}

void MacDockIconHandler::setIcon(const QIcon &icon)
{
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    NSImage *image = nil;
    if (icon.isNull())
        image = [[NSImage imageNamed:@"NSApplicationIcon"] retain];
    else {
        // generate NSImage from QIcon and use this as dock icon.
        QSize size = icon.actualSize(QSize(128, 128));
        QPixmap pixmap = icon.pixmap(size);

        // Perform a QPixmap -> CGImage -> NSImage conversion.
        // This only works for Qt 5.2+ but OS X Armory will never run Qt 5.0 or
        // 5.1.
        image = [[NSImage alloc] initWithCGImage:(QtMac::toCGImageRef(pixmap))
                                 size:(NSSize){128, 128}];

        if(!image) {
            // if testnet image could not be created, load std. app icon
            image = [[NSImage imageNamed:@"NSApplicationIcon"] retain];
        }
    }

    [NSApp setApplicationIconImage:image];
    [image release];
    [pool release];
}

MacDockIconHandler *MacDockIconHandler::instance()
{
    static MacDockIconHandler *s_instance = NULL;
    if (!s_instance)
        s_instance = new MacDockIconHandler();
    return s_instance;
}

void MacDockIconHandler::handleDockIconClickEvent()
{
    if (this->mainWindow)
    {
        this->mainWindow->activateWindow();
        this->mainWindow->show();
    }

    emit this->dockIconClicked();
}
