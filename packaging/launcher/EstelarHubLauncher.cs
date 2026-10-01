using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class EstelarHubLauncher
{
    [STAThread]
    private static int Main(string[] args)
    {
        string applicationDirectory = AppDomain.CurrentDomain.BaseDirectory;
        string qgisRoot = Environment.GetEnvironmentVariable("ESTELAR_QGIS_ROOT");

        if (String.IsNullOrEmpty(qgisRoot))
        {
            string bundledRuntime = Path.Combine(applicationDirectory, "runtime", "qgis");
            if (Directory.Exists(bundledRuntime))
                qgisRoot = bundledRuntime;
        }

        if (String.IsNullOrEmpty(qgisRoot))
            qgisRoot = FindInstalledQgis();

        string qgisLauncher = String.IsNullOrEmpty(qgisRoot)
            ? null
            : Path.Combine(qgisRoot, "bin", "python-qgis.bat");
        string applicationScript = Path.Combine(applicationDirectory, "run_estelar_hub.py");

        if (String.IsNullOrEmpty(qgisLauncher) || !File.Exists(qgisLauncher))
        {
            ShowError("O runtime QGIS 4 não foi encontrado. Reinstale o Estelar Hub ou configure ESTELAR_QGIS_ROOT.");
            return 2;
        }

        if (!File.Exists(applicationScript))
        {
            ShowError("O inicializador Python do Estelar Hub não foi encontrado:\n" + applicationScript);
            return 3;
        }

        try
        {
            string commandProcessor = Environment.GetEnvironmentVariable("ComSpec");
            if (String.IsNullOrEmpty(commandProcessor))
                commandProcessor = "cmd.exe";

            ProcessStartInfo startInfo = new ProcessStartInfo();
            startInfo.FileName = commandProcessor;
            startInfo.Arguments = "/d /s /c \"\"" + qgisLauncher + "\" \"" + applicationScript + "\"\"";
            startInfo.WorkingDirectory = applicationDirectory;
            startInfo.UseShellExecute = false;
            startInfo.CreateNoWindow = true;
            startInfo.WindowStyle = ProcessWindowStyle.Hidden;
            startInfo.EnvironmentVariables["ESTELAR_QGIS_ROOT"] = qgisRoot;

            using (Process process = Process.Start(startInfo))
            {
                if (process == null)
                {
                    ShowError("Não foi possível iniciar o runtime PyQGIS.");
                    return 4;
                }
                process.WaitForExit();
                if (process.ExitCode != 0)
                    ShowError("O Estelar Hub foi encerrado com erro. Consulte o log em AppData\\Local\\Estelar Hub\\logs.");
                return process.ExitCode;
            }
        }
        catch (Exception error)
        {
            ShowError("Falha ao iniciar o Estelar Hub:\n" + error.Message);
            return 5;
        }
    }

    private static string FindInstalledQgis()
    {
        string[] candidates = new string[] {
            @"C:\Program Files\QGIS 4.0.2",
            @"C:\Program Files\QGIS 4.0.1",
            @"C:\Program Files\QGIS 4.0.0",
            @"C:\OSGeo4W"
        };

        foreach (string candidate in candidates)
        {
            if (File.Exists(Path.Combine(candidate, "bin", "python-qgis.bat")))
                return candidate;
        }
        return null;
    }

    private static void ShowError(string message)
    {
        MessageBox.Show(message, "Estelar Hub", MessageBoxButtons.OK, MessageBoxIcon.Error);
    }
}
