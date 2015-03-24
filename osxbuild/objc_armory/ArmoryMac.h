// Copyright (c) 2011-2014 The Bitcoin developers
// Distributed under the MIT/X11 software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

////////////////////////////////////////////////////////////////////////////////
//
// Copyright (C) 2011-2014, Armory Technologies, Inc.
// Distributed under the GNU Affero General Public License (AGPL v3)
// See LICENSE or http://www.gnu.org/licenses/agpl.html
//
////////////////////////////////////////////////////////////////////////////////

// NOTE: If this file is altered, you MUST sync the changes with ArmoryMac.sip.

#ifndef ARMORYMAC_H
#define ARMORYMAC_H

#include <QtWidgets/QMainWindow>
#include <QtCore/QObject>

QT_BEGIN_NAMESPACE
class QIcon;
class QMenu;
class QWidget;
QT_END_NAMESPACE

#ifdef __OBJC__
@class DockIconClickEventHandler;
#else
class DockIconClickEventHandler;
#endif

/** Macintosh-specific dock icon handler.
 */
class MacDockIconHandler : public QObject
{
    Q_OBJECT

public:
    ~MacDockIconHandler();

    QMenu *dockMenu();
    void setIcon(const QIcon &icon);
    void setMainWindow(QMainWindow *window);
    static MacDockIconHandler *instance();

    void handleDockIconClickEvent();

signals:
    void dockIconClicked();

private:
    MacDockIconHandler();

    DockIconClickEventHandler *m_dockIconClickEventHandler;
    QWidget *m_dummyWidget;
    QMenu *m_dockMenu;
    QMainWindow *mainWindow;
};


/** Macintosh-specific utilities */
class MacUtils : public QObject
{
    Q_OBJECT

public:
    /** Careate a file open dialog */
    QString openFile();
    static MacUtils *instance();
};
#endif // ARMORYMAC_H
