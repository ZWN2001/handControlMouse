import wx
import wx.adv

from main import Detector


class FolderBookmarkTaskBarIcon(wx.adv.TaskBarIcon):
    ICON = 'hand.png'
    TITLE = '手控鼠标'
    paused = False
    MENU_ID1, MENU_ID2, MENU_ID3 = wx.NewIdRef(count=3)
    de = None

    def __init__(self):
        super().__init__()

        # 设置图标和提示
        self.SetIcon(wx.Icon(self.ICON), self.TITLE)

        # 绑定菜单项事件
        self.Bind(wx.EVT_MENU, self.onPause, id=self.MENU_ID1)
        self.Bind(wx.EVT_MENU, self.onResume, id=self.MENU_ID2)
        self.Bind(wx.EVT_MENU, self.onExit, id=self.MENU_ID3)

        self.de = Detector()
        self.de.startDetect()

    def CreatePopupMenu(self):
        menu = wx.Menu()
        if self.paused:
            menu.Append(self.MENU_ID2, '恢复')
            menu.Append(self.MENU_ID3, '退出')
            return menu
        else:
            menu.Append(self.MENU_ID1, '暂停')
            menu.Append(self.MENU_ID3, '退出')
            return menu

    def onExit(self, event):
        self.de.exit()
        wx.Exit()

    def onPause(self, event):
        self.paused = True
        self.de.pause()

    def onResume(self, event):
        self.paused = False
        self.de.reStart()


class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__()
        FolderBookmarkTaskBarIcon()


class MyApp(wx.App):
    def OnInit(self):
        MyFrame()
        return True


if __name__ == '__main__':
    app = MyApp()
    app.MainLoop()
