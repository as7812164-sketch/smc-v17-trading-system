.class Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;
.super Landroid/webkit/WebViewClient;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->j()Landroid/webkit/WebViewClient;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;


# direct methods
.method constructor <init>(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)V
    .locals 0

    .line 1
    iput-object p1, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 2
    .line 3
    invoke-direct {p0}, Landroid/webkit/WebViewClient;-><init>()V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method private a(Landroid/net/Uri;)Z
    .locals 2

    .line 1
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 2
    .line 3
    invoke-static {v0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->g(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Ljava/util/List;

    .line 4
    .line 5
    .line 6
    move-result-object v0

    .line 7
    invoke-interface {v0}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    .line 8
    .line 9
    .line 10
    move-result-object v0

    .line 11
    :cond_0
    invoke-interface {v0}, Ljava/util/Iterator;->hasNext()Z

    .line 12
    .line 13
    .line 14
    move-result v1

    .line 15
    if-eqz v1, :cond_1

    .line 16
    .line 17
    invoke-interface {v0}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    .line 18
    .line 19
    .line 20
    move-result-object v1

    .line 21
    check-cast v1, Landroid/net/Uri;

    .line 22
    .line 23
    invoke-direct {p0, v1, p1}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->c(Landroid/net/Uri;Landroid/net/Uri;)Z

    .line 24
    .line 25
    .line 26
    move-result v1

    .line 27
    if-eqz v1, :cond_0

    .line 28
    .line 29
    const/4 p1, 0x1

    .line 30
    return p1

    .line 31
    :cond_1
    const/4 p1, 0x0

    .line 32
    return p1
.end method

.method private b(Landroid/net/Uri;)Z
    .locals 3

    .line 1
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 2
    .line 3
    invoke-static {v0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->d(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Landroid/net/Uri;

    .line 4
    .line 5
    .line 6
    move-result-object v0

    .line 7
    invoke-virtual {p1}, Landroid/net/Uri;->getScheme()Ljava/lang/String;

    .line 8
    .line 9
    .line 10
    move-result-object v1

    .line 11
    const-string v2, "data"

    .line 12
    .line 13
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 14
    .line 15
    .line 16
    move-result v1

    .line 17
    const/4 v2, 0x0

    .line 18
    if-nez v1, :cond_0

    .line 19
    .line 20
    invoke-direct {p0, p1, v0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->c(Landroid/net/Uri;Landroid/net/Uri;)Z

    .line 21
    .line 22
    .line 23
    move-result v0

    .line 24
    if-nez v0, :cond_0

    .line 25
    .line 26
    invoke-direct {p0, p1}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a(Landroid/net/Uri;)Z

    .line 27
    .line 28
    .line 29
    move-result v0

    .line 30
    if-nez v0, :cond_0

    .line 31
    .line 32
    :try_start_0
    new-instance v0, Ln/d$e;

    .line 33
    .line 34
    invoke-direct {v0}, Ln/d$e;-><init>()V

    .line 35
    .line 36
    .line 37
    iget-object v1, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 38
    .line 39
    invoke-static {v1}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->e(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)I

    .line 40
    .line 41
    .line 42
    move-result v1

    .line 43
    invoke-virtual {v0, v1}, Ln/d$e;->k(I)Ln/d$e;

    .line 44
    .line 45
    .line 46
    move-result-object v0

    .line 47
    invoke-virtual {v0}, Ln/d$e;->a()Ln/d;

    .line 48
    .line 49
    .line 50
    move-result-object v0

    .line 51
    iget-object v1, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 52
    .line 53
    invoke-virtual {v0, v1, p1}, Ln/d;->c(Landroid/content/Context;Landroid/net/Uri;)V
    :try_end_0
    .catch Landroid/content/ActivityNotFoundException; {:try_start_0 .. :try_end_0} :catch_0

    .line 54
    .line 55
    .line 56
    const/4 p1, 0x1

    .line 57
    return p1

    .line 58
    :catch_0
    invoke-static {}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->f()Ljava/lang/String;

    .line 59
    .line 60
    .line 61
    move-result-object v0

    .line 62
    const-string v1, "ActivityNotFoundException while launching \'%s\'"

    .line 63
    .line 64
    filled-new-array {p1}, [Ljava/lang/Object;

    .line 65
    .line 66
    .line 67
    move-result-object p1

    .line 68
    invoke-static {v1, p1}, Ljava/lang/String;->format(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    .line 69
    .line 70
    .line 71
    move-result-object p1

    .line 72
    invoke-static {v0, p1}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    .line 73
    .line 74
    .line 75
    :cond_0
    return v2
.end method

.method private c(Landroid/net/Uri;Landroid/net/Uri;)Z
    .locals 2

    .line 1
    invoke-virtual {p1}, Landroid/net/Uri;->getScheme()Ljava/lang/String;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    invoke-virtual {p2}, Landroid/net/Uri;->getScheme()Ljava/lang/String;

    .line 6
    .line 7
    .line 8
    move-result-object v1

    .line 9
    invoke-virtual {v0, v1}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    .line 10
    .line 11
    .line 12
    move-result v0

    .line 13
    if-eqz v0, :cond_0

    .line 14
    .line 15
    invoke-virtual {p1}, Landroid/net/Uri;->getHost()Ljava/lang/String;

    .line 16
    .line 17
    .line 18
    move-result-object v0

    .line 19
    invoke-virtual {p2}, Landroid/net/Uri;->getHost()Ljava/lang/String;

    .line 20
    .line 21
    .line 22
    move-result-object v1

    .line 23
    invoke-virtual {v0, v1}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    .line 24
    .line 25
    .line 26
    move-result v0

    .line 27
    if-eqz v0, :cond_0

    .line 28
    .line 29
    invoke-virtual {p1}, Landroid/net/Uri;->getPort()I

    .line 30
    .line 31
    .line 32
    move-result p1

    .line 33
    invoke-virtual {p2}, Landroid/net/Uri;->getPort()I

    .line 34
    .line 35
    .line 36
    move-result p2

    .line 37
    if-ne p1, p2, :cond_0

    .line 38
    .line 39
    const/4 p1, 0x1

    .line 40
    return p1

    .line 41
    :cond_0
    const/4 p1, 0x0

    .line 42
    return p1
.end method


# virtual methods
.method public onRenderProcessGone(Landroid/webkit/WebView;Landroid/webkit/RenderProcessGoneDetail;)Z
    .locals 3

    .line 1
    invoke-virtual {p1}, Landroid/view/View;->getParent()Landroid/view/ViewParent;

    .line 2
    .line 3
    .line 4
    move-result-object p2

    .line 5
    check-cast p2, Landroid/view/ViewGroup;

    .line 6
    .line 7
    invoke-virtual {p2, p1}, Landroid/view/ViewGroup;->removeView(Landroid/view/View;)V

    .line 8
    .line 9
    .line 10
    invoke-virtual {p1}, Landroid/webkit/WebView;->destroy()V

    .line 11
    .line 12
    .line 13
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 14
    .line 15
    new-instance v1, Landroid/webkit/WebView;

    .line 16
    .line 17
    invoke-virtual {p1}, Landroid/view/View;->getContext()Landroid/content/Context;

    .line 18
    .line 19
    .line 20
    move-result-object v2

    .line 21
    invoke-direct {v1, v2}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V

    .line 22
    .line 23
    .line 24
    invoke-static {v0, v1}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->b(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;Landroid/webkit/WebView;)Landroid/webkit/WebView;

    .line 25
    .line 26
    .line 27
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 28
    .line 29
    invoke-static {v0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->a(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Landroid/webkit/WebView;

    .line 30
    .line 31
    .line 32
    move-result-object v0

    .line 33
    invoke-virtual {v0, p0}, Landroid/webkit/WebView;->setWebViewClient(Landroid/webkit/WebViewClient;)V

    .line 34
    .line 35
    .line 36
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 37
    .line 38
    invoke-static {v0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->a(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Landroid/webkit/WebView;

    .line 39
    .line 40
    .line 41
    move-result-object v0

    .line 42
    invoke-virtual {v0}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;

    .line 43
    .line 44
    .line 45
    move-result-object v0

    .line 46
    invoke-static {v0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c(Landroid/webkit/WebSettings;)V

    .line 47
    .line 48
    .line 49
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 50
    .line 51
    invoke-static {v0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->a(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Landroid/webkit/WebView;

    .line 52
    .line 53
    .line 54
    move-result-object v0

    .line 55
    invoke-virtual {p2, v0}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V

    .line 56
    .line 57
    .line 58
    invoke-virtual {p1}, Landroid/view/View;->getContext()Landroid/content/Context;

    .line 59
    .line 60
    .line 61
    move-result-object p1

    .line 62
    const-string p2, "Recovering from crash"

    .line 63
    .line 64
    const/4 v0, 0x1

    .line 65
    invoke-static {p1, p2, v0}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;

    .line 66
    .line 67
    .line 68
    move-result-object p1

    .line 69
    invoke-virtual {p1}, Landroid/widget/Toast;->show()V

    .line 70
    .line 71
    .line 72
    iget-object p1, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 73
    .line 74
    invoke-static {p1}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->a(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Landroid/webkit/WebView;

    .line 75
    .line 76
    .line 77
    move-result-object p1

    .line 78
    iget-object p2, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->a:Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 79
    .line 80
    invoke-static {p2}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->d(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Landroid/net/Uri;

    .line 81
    .line 82
    .line 83
    move-result-object p2

    .line 84
    invoke-virtual {p2}, Landroid/net/Uri;->toString()Ljava/lang/String;

    .line 85
    .line 86
    .line 87
    move-result-object p2

    .line 88
    invoke-virtual {p1, p2}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V

    .line 89
    .line 90
    .line 91
    return v0
.end method

.method public shouldOverrideUrlLoading(Landroid/webkit/WebView;Landroid/webkit/WebResourceRequest;)Z
    .locals 0

    .line 2
    invoke-interface {p2}, Landroid/webkit/WebResourceRequest;->getUrl()Landroid/net/Uri;

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->b(Landroid/net/Uri;)Z

    move-result p1

    return p1
.end method

.method public shouldOverrideUrlLoading(Landroid/webkit/WebView;Ljava/lang/String;)Z
    .locals 0

    .line 1
    invoke-static {p2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;->b(Landroid/net/Uri;)Z

    move-result p1

    return p1
.end method
