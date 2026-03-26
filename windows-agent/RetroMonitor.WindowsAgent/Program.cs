using RetroMonitor.WindowsAgent.Configuration;
using RetroMonitor.WindowsAgent.Services;

if (args.Contains("--dump-sensors", StringComparer.OrdinalIgnoreCase))
{
    using var dumpReader = new HardwareMonitorReader();
    Console.WriteLine(dumpReader.DumpSensorsJson());
    return;
}

var builder = WebApplication.CreateBuilder(args);

builder.Host.UseWindowsService();
builder.Services.Configure<AgentOptions>(builder.Configuration.GetSection("RetroMonitor"));
builder.Services.AddSingleton<SystemMetricsReader>();
builder.Services.AddSingleton<HardwareMonitorReader>();
builder.Services.AddSingleton<WindowsTelemetryProvider>();
builder.Services.AddSingleton<TelemetrySampler>();
builder.Services.AddSingleton<IHostedService>(sp => sp.GetRequiredService<TelemetrySampler>());

var bootOptions = builder.Configuration.GetSection("RetroMonitor").Get<AgentOptions>() ?? new AgentOptions();
builder.WebHost.UseUrls($"http://{bootOptions.Host}:{bootOptions.Port}");

var app = builder.Build();

app.MapGet("/telemetry", (TelemetrySampler sampler) =>
{
    var snapshot = sampler.Current();
    return snapshot is null
        ? Results.Problem("telemetry unavailable", statusCode: StatusCodes.Status503ServiceUnavailable)
        : Results.Json(snapshot);
});

app.Run();
