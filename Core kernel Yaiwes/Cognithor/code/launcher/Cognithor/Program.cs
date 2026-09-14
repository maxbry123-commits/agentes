using System;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace Cognithor;

static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        // ------------------------------------------------------------------
        // Single-instance guard.
        // ------------------------------------------------------------------
        // NOTE: Mutex must be stored for the process lifetime (don't `using`
        // it — that would dispose it at first return and defeat the guard).
        var mutex = new Mutex(true, @"Global\CognithorAppShell", out bool created);
        if (!created)
        {
            MessageBox.Show(
                "Cognithor is already running.\nCheck the system tray.",
                "Cognithor",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information);
            mutex.Dispose();
            return;
        }

        Application.EnableVisualStyles();
        Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);
        Application.SetCompatibleTextRenderingDefault(false);

        // ------------------------------------------------------------------
        // Crash handling. A silent exception in AppShell() would previously
        // make the EXE vanish from Task Manager without trace — no window,
        // no log. We now surface any fatal error via MessageBox and write a
        // crash log under %LOCALAPPDATA%\Cognithor\.
        // ------------------------------------------------------------------
        Application.ThreadException += (s, e) => ReportFatal(e.Exception, "ThreadException");
        AppDomain.CurrentDomain.UnhandledException += (s, e) =>
            ReportFatal(e.ExceptionObject as Exception, "UnhandledException");

        AppShell? shell = null;
        try
        {
            shell = new AppShell(args);
            Application.Run();
        }
        catch (Exception exc)
        {
            ReportFatal(exc, "Startup");
            return;
        }
        finally
        {
            shell?.Dispose();
            mutex.ReleaseMutex();
            mutex.Dispose();
        }
    }

    static void ReportFatal(Exception? exc, string context)
    {
        if (exc is null) return;
        try
        {
            var dir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Cognithor");
            Directory.CreateDirectory(dir);
            var log = Path.Combine(dir, "launcher-crash.log");
            var now = DateTime.UtcNow.ToString("o");
            File.AppendAllText(
                log,
                $"[{now}] {context}: {exc.GetType().FullName}: {exc.Message}\n" +
                $"{exc.StackTrace}\n\n");
            MessageBox.Show(
                $"Cognithor launcher failed to start.\n\n" +
                $"{exc.GetType().Name}: {exc.Message}\n\n" +
                $"Details written to:\n{log}",
                "Cognithor — Startup Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
        }
        catch
        {
            // Last-resort: just show the error without logging.
            try
            {
                MessageBox.Show(
                    $"Cognithor launcher failed: {exc.Message}",
                    "Cognithor",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
            }
            catch { /* really nothing we can do now */ }
        }
    }
}
