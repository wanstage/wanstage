using Google.Apis.Auth.OAuth2;
using Google.Apis.Services;
using Google.Apis.Util.Store;
using Google.Apis.YouTube.v3;
using Google.Apis.YouTube.v3.Data;

class Program
{
    static readonly string[] Scopes = { YouTubeService.Scope.YoutubeUpload };

    static async Task Main(string[] args)
    {
        var filePath = GetArg(args, "--file") ?? "../out/out.mp4";
        var title    = GetArg(args, "--title") ?? "WANSTAGE Upload Test";
        var desc     = GetArg(args, "--desc")  ?? "Uploaded from .NET sample";
        var privacy  = GetArg(args, "--privacy") ?? "unlisted";
        var clientJsonPath = GetArg(args, "--client");

        if (!File.Exists(filePath))
        {
            Console.Error.WriteLine($"File not found: {filePath}");
            Environment.Exit(2);
        }

        UserCredential credential;

        if (!string.IsNullOrEmpty(clientJsonPath) && File.Exists(clientJsonPath))
        {
            using var stream = new FileStream(clientJsonPath, FileMode.Open, FileAccess.Read);
            credential = await GoogleWebAuthorizationBroker.AuthorizeAsync(
                GoogleClientSecrets.FromStream(stream).Secrets,
                Scopes, "user", CancellationToken.None, new FileDataStore("token_store", true));
        }
        else
        {
            var cid  = Environment.GetEnvironmentVariable("YT_CLIENT_ID");
            var csec = Environment.GetEnvironmentVariable("YT_CLIENT_SECRET");
            if (string.IsNullOrWhiteSpace(cid) || string.IsNullOrWhiteSpace(csec))
            {
                Console.Error.WriteLine("Set YT_CLIENT_ID / YT_CLIENT_SECRET or pass --client=client_secret.json");
                Environment.Exit(3);
                return;
            }
            var secrets = new ClientSecrets { ClientId = cid, ClientSecret = csec };
            credential = await GoogleWebAuthorizationBroker.AuthorizeAsync(
                secrets,
                Scopes, "user", CancellationToken.None, new FileDataStore("token_store", true));
        }

        var youtube = new YouTubeService(new BaseClientService.Initializer
        {
            HttpClientInitializer = credential,
            ApplicationName = "WanstageYoutube"
        });

        var video = new Video
        {
            Snippet = new VideoSnippet { Title = title, Description = desc },
            Status  = new VideoStatus   { PrivacyStatus = privacy }
        };

        using var fs = new FileStream(filePath, FileMode.Open, FileAccess.Read);
        var insert = youtube.Videos.Insert(video, "snippet,status", fs, "video/*");

        Console.WriteLine("Uploading...");
        await insert.UploadAsync();

        Console.WriteLine(insert.ResponseBody != null
            ? $"✅ Done: https://youtu.be/{insert.ResponseBody.Id}"
            : "⚠️ Upload finished but no video id returned.");
    }

    static string? GetArg(string[] args, string name)
    {
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == name && i + 1 < args.Length) return args[i + 1];
            if (args[i].StartsWith(name + "=", StringComparison.Ordinal))
                return args[i].Substring(name.Length + 1);
        }
        return null;
    }
}
