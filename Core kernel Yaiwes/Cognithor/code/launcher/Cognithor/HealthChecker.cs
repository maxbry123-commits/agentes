using System;
using System.Net.Http;
using System.Windows.Forms;

namespace Cognithor;

enum AppStatus { Starting, Healthy, Unhealthy, Stopped }

sealed class HealthChecker : IDisposable
{
    readonly HttpClient _http;
    readonly System.Windows.Forms.Timer _timer;
    AppStatus _lastStatus = AppStatus.Starting;

    public event Action<AppStatus, AppStatus>? StatusChanged;
    public AppStatus CurrentStatus => _lastStatus;

    public HealthChecker(int intervalMs = 10_000)
    {
        _http = new HttpClient { Timeout = TimeSpan.FromSeconds(3) };
        _timer = new System.Windows.Forms.Timer { Interval = intervalMs };
        _timer.Tick += async (_, _) => await PollAsync();
    }

    public void Start() => _timer.Start();
    public void Stop() => _timer.Stop();

    async System.Threading.Tasks.Task PollAsync()
    {
        AppStatus newStatus;
        try
        {
            var resp = await _http.GetAsync("http://localhost:8741/api/v1/health");
            newStatus = resp.IsSuccessStatusCode ? AppStatus.Healthy : AppStatus.Unhealthy;
        }
        catch
        {
            newStatus = AppStatus.Stopped;
        }

        if (newStatus != _lastStatus)
        {
            var prev = _lastStatus;
            _lastStatus = newStatus;
            StatusChanged?.Invoke(prev, newStatus);
        }
    }

    public void Dispose()
    {
        _timer.Stop();
        _timer.Dispose();
        _http.Dispose();
    }
}
