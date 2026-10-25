.class public Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;
.super Landroid/app/Activity;
.source "SourceFile"


# static fields
.field private static final e:Ljava/lang/String; = "WebViewFallbackActivity"


# instance fields
.field private a:Landroid/net/Uri;

.field private b:I

.field private c:Landroid/webkit/WebView;

.field private d:Ljava/util/List;


# direct methods
.method static constructor <clinit>()V
    .locals 0

    return-void
.end method

.method public constructor <init>()V
    .locals 1

    .line 1
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V

    .line 2
    .line 3
    .line 4
    new-instance v0, Ljava/util/ArrayList;

    .line 5
    .line 6
    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V

    .line 7
    .line 8
    .line 9
    iput-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->d:Ljava/util/List;

    .line 10
    .line 11
    return-void
.end method

.method static synthetic a(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Landroid/webkit/WebView;
    .locals 0

    .line 1
    iget-object p0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 2
    .line 3
    return-object p0
.end method

.method static synthetic b(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;Landroid/webkit/WebView;)Landroid/webkit/WebView;
    .locals 0

    .line 1
    iput-object p1, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 2
    .line 3
    return-object p1
.end method

.method static synthetic c(Landroid/webkit/WebSettings;)V
    .locals 0

    .line 1
    invoke-static {p0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->k(Landroid/webkit/WebSettings;)V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method static synthetic d(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Landroid/net/Uri;
    .locals 0

    .line 1
    iget-object p0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->a:Landroid/net/Uri;

    .line 2
    .line 3
    return-object p0
.end method

.method static synthetic e(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)I
    .locals 0

    .line 1
    iget p0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->b:I

    .line 2
    .line 3
    return p0
.end method

.method static synthetic f()Ljava/lang/String;
    .locals 1

    .line 1
    sget-object v0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->e:Ljava/lang/String;

    .line 2
    .line 3
    return-object v0
.end method

.method static synthetic g(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)Ljava/util/List;
    .locals 0

    .line 1
    iget-object p0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->d:Ljava/util/List;

    .line 2
    .line 3
    return-object p0
.end method

.method public static h(Landroid/content/Context;Landroid/net/Uri;LK/i;)Landroid/content/Intent;
    .locals 2

    .line 1
    new-instance v0, Landroid/content/Intent;

    .line 2
    .line 3
    const-class v1, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;

    .line 4
    .line 5
    invoke-direct {v0, p0, v1}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    .line 6
    .line 7
    .line 8
    const-string v1, "com.google.browser.examples.twawebviewfallback.WebViewFallbackActivity.LAUNCH_URL"

    .line 9
    .line 10
    invoke-virtual {v0, v1, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Landroid/os/Parcelable;)Landroid/content/Intent;

    .line 11
    .line 12
    .line 13
    iget p1, p2, LK/i;->b:I

    .line 14
    .line 15
    invoke-static {p0, p1}, Landroidx/core/content/a;->a(Landroid/content/Context;I)I

    .line 16
    .line 17
    .line 18
    move-result p1

    .line 19
    const-string v1, "com.google.browser.examples.twawebviewfallback.WebViewFallbackActivity.KEY_STATUS_BAR_COLOR"

    .line 20
    .line 21
    invoke-virtual {v0, v1, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    .line 22
    .line 23
    .line 24
    iget p1, p2, LK/i;->d:I

    .line 25
    .line 26
    invoke-static {p0, p1}, Landroidx/core/content/a;->a(Landroid/content/Context;I)I

    .line 27
    .line 28
    .line 29
    move-result p0

    .line 30
    const-string p1, "com.google.browser.examples.twawebviewfallback.WebViewFallbackActivity.KEY_NAVIGATION_BAR_COLOR"

    .line 31
    .line 32
    invoke-virtual {v0, p1, p0}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    .line 33
    .line 34
    .line 35
    iget-object p0, p2, LK/i;->l:Ljava/util/List;

    .line 36
    .line 37
    if-eqz p0, :cond_0

    .line 38
    .line 39
    new-instance p0, Ljava/util/ArrayList;

    .line 40
    .line 41
    iget-object p1, p2, LK/i;->l:Ljava/util/List;

    .line 42
    .line 43
    invoke-direct {p0, p1}, Ljava/util/ArrayList;-><init>(Ljava/util/Collection;)V

    .line 44
    .line 45
    .line 46
    const-string p1, "com.google.browser.examples.twawebviewfallback.WebViewFallbackActivity.KEY_EXTRA_ORIGINS"

    .line 47
    .line 48
    invoke-virtual {v0, p1, p0}, Landroid/content/Intent;->putStringArrayListExtra(Ljava/lang/String;Ljava/util/ArrayList;)Landroid/content/Intent;

    .line 49
    .line 50
    .line 51
    :cond_0
    return-object v0
.end method

.method private i()Landroid/webkit/WebChromeClient;
    .locals 1

    .line 1
    new-instance v0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$b;

    .line 2
    .line 3
    invoke-direct {v0, p0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$b;-><init>(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)V

    .line 4
    .line 5
    .line 6
    return-object v0
.end method

.method private j()Landroid/webkit/WebViewClient;
    .locals 1

    .line 1
    new-instance v0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;

    .line 2
    .line 3
    invoke-direct {v0, p0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity$a;-><init>(Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;)V

    .line 4
    .line 5
    .line 6
    return-object v0
.end method

.method private static k(Landroid/webkit/WebSettings;)V
    .locals 1

    .line 1
    const/4 v0, 0x1

    .line 2
    invoke-virtual {p0, v0}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V

    .line 3
    .line 4
    .line 5
    invoke-virtual {p0, v0}, Landroid/webkit/WebSettings;->setDomStorageEnabled(Z)V

    .line 6
    .line 7
    .line 8
    invoke-virtual {p0, v0}, Landroid/webkit/WebSettings;->setDatabaseEnabled(Z)V

    .line 9
    .line 10
    .line 11
    const/4 v0, 0x0

    .line 12
    invoke-virtual {p0, v0}, Landroid/webkit/WebSettings;->setMediaPlaybackRequiresUserGesture(Z)V

    .line 13
    .line 14
    .line 15
    return-void
.end method


# virtual methods
.method public onConfigurationChanged(Landroid/content/res/Configuration;)V
    .locals 0

    .line 1
    invoke-super {p0, p1}, Landroid/app/Activity;->onConfigurationChanged(Landroid/content/res/Configuration;)V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .locals 6

    .line 1
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    .line 2
    .line 3
    .line 4
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 5
    .line 6
    .line 7
    move-result-object v0

    .line 8
    const-string v1, "com.google.browser.examples.twawebviewfallback.WebViewFallbackActivity.LAUNCH_URL"

    .line 9
    .line 10
    invoke-virtual {v0, v1}, Landroid/content/Intent;->getParcelableExtra(Ljava/lang/String;)Landroid/os/Parcelable;

    .line 11
    .line 12
    .line 13
    move-result-object v0

    .line 14
    check-cast v0, Landroid/net/Uri;

    .line 15
    .line 16
    iput-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->a:Landroid/net/Uri;

    .line 17
    .line 18
    invoke-virtual {v0}, Landroid/net/Uri;->getScheme()Ljava/lang/String;

    .line 19
    .line 20
    .line 21
    move-result-object v0

    .line 22
    const-string v1, "https"

    .line 23
    .line 24
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 25
    .line 26
    .line 27
    move-result v0

    .line 28
    if-eqz v0, :cond_5

    .line 29
    .line 30
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 31
    .line 32
    .line 33
    move-result-object v0

    .line 34
    const-string v2, "com.google.browser.examples.twawebviewfallback.WebViewFallbackActivity.KEY_NAVIGATION_BAR_COLOR"

    .line 35
    .line 36
    invoke-virtual {v0, v2}, Landroid/content/Intent;->hasExtra(Ljava/lang/String;)Z

    .line 37
    .line 38
    .line 39
    move-result v0

    .line 40
    const/4 v3, 0x0

    .line 41
    if-eqz v0, :cond_0

    .line 42
    .line 43
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 44
    .line 45
    .line 46
    move-result-object v0

    .line 47
    invoke-virtual {v0, v2, v3}, Landroid/content/Intent;->getIntExtra(Ljava/lang/String;I)I

    .line 48
    .line 49
    .line 50
    move-result v0

    .line 51
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    .line 52
    .line 53
    .line 54
    move-result-object v2

    .line 55
    invoke-virtual {v2, v0}, Landroid/view/Window;->setNavigationBarColor(I)V

    .line 56
    .line 57
    .line 58
    :cond_0
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 59
    .line 60
    .line 61
    move-result-object v0

    .line 62
    const-string v2, "com.google.browser.examples.twawebviewfallback.WebViewFallbackActivity.KEY_STATUS_BAR_COLOR"

    .line 63
    .line 64
    invoke-virtual {v0, v2}, Landroid/content/Intent;->hasExtra(Ljava/lang/String;)Z

    .line 65
    .line 66
    .line 67
    move-result v0

    .line 68
    if-eqz v0, :cond_1

    .line 69
    .line 70
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 71
    .line 72
    .line 73
    move-result-object v0

    .line 74
    invoke-virtual {v0, v2, v3}, Landroid/content/Intent;->getIntExtra(Ljava/lang/String;I)I

    .line 75
    .line 76
    .line 77
    move-result v0

    .line 78
    iput v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->b:I

    .line 79
    .line 80
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    .line 81
    .line 82
    .line 83
    move-result-object v0

    .line 84
    iget v2, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->b:I

    .line 85
    .line 86
    invoke-virtual {v0, v2}, Landroid/view/Window;->setStatusBarColor(I)V

    .line 87
    .line 88
    .line 89
    goto :goto_0

    .line 90
    :cond_1
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    .line 91
    .line 92
    .line 93
    move-result-object v0

    .line 94
    invoke-virtual {v0}, Landroid/view/Window;->getStatusBarColor()I

    .line 95
    .line 96
    .line 97
    move-result v0

    .line 98
    iput v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->b:I

    .line 99
    .line 100
    :goto_0
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 101
    .line 102
    .line 103
    move-result-object v0

    .line 104
    const-string v2, "com.google.browser.examples.twawebviewfallback.WebViewFallbackActivity.KEY_EXTRA_ORIGINS"

    .line 105
    .line 106
    invoke-virtual {v0, v2}, Landroid/content/Intent;->hasExtra(Ljava/lang/String;)Z

    .line 107
    .line 108
    .line 109
    move-result v0

    .line 110
    if-eqz v0, :cond_3

    .line 111
    .line 112
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 113
    .line 114
    .line 115
    move-result-object v0

    .line 116
    invoke-virtual {v0, v2}, Landroid/content/Intent;->getStringArrayListExtra(Ljava/lang/String;)Ljava/util/ArrayList;

    .line 117
    .line 118
    .line 119
    move-result-object v0

    .line 120
    if-eqz v0, :cond_3

    .line 121
    .line 122
    invoke-interface {v0}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    .line 123
    .line 124
    .line 125
    move-result-object v0

    .line 126
    :goto_1
    invoke-interface {v0}, Ljava/util/Iterator;->hasNext()Z

    .line 127
    .line 128
    .line 129
    move-result v2

    .line 130
    if-eqz v2, :cond_3

    .line 131
    .line 132
    invoke-interface {v0}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    .line 133
    .line 134
    .line 135
    move-result-object v2

    .line 136
    check-cast v2, Ljava/lang/String;

    .line 137
    .line 138
    invoke-static {v2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    .line 139
    .line 140
    .line 141
    move-result-object v3

    .line 142
    invoke-virtual {v3}, Landroid/net/Uri;->getScheme()Ljava/lang/String;

    .line 143
    .line 144
    .line 145
    move-result-object v4

    .line 146
    invoke-virtual {v1, v4}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    .line 147
    .line 148
    .line 149
    move-result v4

    .line 150
    if-nez v4, :cond_2

    .line 151
    .line 152
    sget-object v3, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->e:Ljava/lang/String;

    .line 153
    .line 154
    new-instance v4, Ljava/lang/StringBuilder;

    .line 155
    .line 156
    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    .line 157
    .line 158
    .line 159
    const-string v5, "Only \'https\' origins are accepted. Ignoring extra origin: "

    .line 160
    .line 161
    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 162
    .line 163
    .line 164
    invoke-virtual {v4, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 165
    .line 166
    .line 167
    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 168
    .line 169
    .line 170
    move-result-object v2

    .line 171
    invoke-static {v3, v2}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 172
    .line 173
    .line 174
    goto :goto_1

    .line 175
    :cond_2
    iget-object v2, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->d:Ljava/util/List;

    .line 176
    .line 177
    invoke-interface {v2, v3}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 178
    .line 179
    .line 180
    goto :goto_1

    .line 181
    :cond_3
    new-instance v0, Landroid/webkit/WebView;

    .line 182
    .line 183
    invoke-direct {v0, p0}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V

    .line 184
    .line 185
    .line 186
    iput-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 187
    .line 188
    invoke-direct {p0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->j()Landroid/webkit/WebViewClient;

    .line 189
    .line 190
    .line 191
    move-result-object v1

    .line 192
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->setWebViewClient(Landroid/webkit/WebViewClient;)V

    .line 193
    .line 194
    .line 195
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 196
    .line 197
    invoke-direct {p0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->i()Landroid/webkit/WebChromeClient;

    .line 198
    .line 199
    .line 200
    move-result-object v1

    .line 201
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->setWebChromeClient(Landroid/webkit/WebChromeClient;)V

    .line 202
    .line 203
    .line 204
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 205
    .line 206
    invoke-virtual {v0}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;

    .line 207
    .line 208
    .line 209
    move-result-object v0

    .line 210
    invoke-static {v0}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->k(Landroid/webkit/WebSettings;)V

    .line 211
    .line 212
    .line 213
    new-instance v0, Landroid/view/ViewGroup$LayoutParams;

    .line 214
    .line 215
    const/4 v1, -0x1

    .line 216
    invoke-direct {v0, v1, v1}, Landroid/view/ViewGroup$LayoutParams;-><init>(II)V

    .line 217
    .line 218
    .line 219
    iget-object v1, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 220
    .line 221
    invoke-virtual {p0, v1, v0}, Landroid/app/Activity;->setContentView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 222
    .line 223
    .line 224
    if-eqz p1, :cond_4

    .line 225
    .line 226
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 227
    .line 228
    invoke-virtual {v0, p1}, Landroid/webkit/WebView;->restoreState(Landroid/os/Bundle;)Landroid/webkit/WebBackForwardList;

    .line 229
    .line 230
    .line 231
    return-void

    .line 232
    :cond_4
    new-instance p1, Ljava/util/HashMap;

    .line 233
    .line 234
    invoke-direct {p1}, Ljava/util/HashMap;-><init>()V

    .line 235
    .line 236
    .line 237
    new-instance v0, Ljava/lang/StringBuilder;

    .line 238
    .line 239
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    .line 240
    .line 241
    .line 242
    const-string v1, "android-app://"

    .line 243
    .line 244
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 245
    .line 246
    .line 247
    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    .line 248
    .line 249
    .line 250
    move-result-object v1

    .line 251
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 252
    .line 253
    .line 254
    const-string v1, "/"

    .line 255
    .line 256
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 257
    .line 258
    .line 259
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 260
    .line 261
    .line 262
    move-result-object v0

    .line 263
    const-string v1, "Referer"

    .line 264
    .line 265
    invoke-interface {p1, v1, v0}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 266
    .line 267
    .line 268
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 269
    .line 270
    iget-object v1, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->a:Landroid/net/Uri;

    .line 271
    .line 272
    invoke-virtual {v1}, Landroid/net/Uri;->toString()Ljava/lang/String;

    .line 273
    .line 274
    .line 275
    move-result-object v1

    .line 276
    invoke-virtual {v0, v1, p1}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;Ljava/util/Map;)V

    .line 277
    .line 278
    .line 279
    return-void

    .line 280
    :cond_5
    new-instance p1, Ljava/lang/IllegalArgumentException;

    .line 281
    .line 282
    const-string v0, "launchUrl scheme must be \'https\'"

    .line 283
    .line 284
    invoke-direct {p1, v0}, Ljava/lang/IllegalArgumentException;-><init>(Ljava/lang/String;)V

    .line 285
    .line 286
    .line 287
    throw p1
.end method

.method public onKeyDown(ILandroid/view/KeyEvent;)Z
    .locals 1

    .line 1
    const/4 v0, 0x4

    .line 2
    if-ne p1, v0, :cond_0

    .line 3
    .line 4
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 5
    .line 6
    invoke-virtual {v0}, Landroid/webkit/WebView;->canGoBack()Z

    .line 7
    .line 8
    .line 9
    move-result v0

    .line 10
    if-eqz v0, :cond_0

    .line 11
    .line 12
    iget-object p1, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 13
    .line 14
    invoke-virtual {p1}, Landroid/webkit/WebView;->goBack()V

    .line 15
    .line 16
    .line 17
    const/4 p1, 0x1

    .line 18
    return p1

    .line 19
    :cond_0
    invoke-super {p0, p1, p2}, Landroid/app/Activity;->onKeyDown(ILandroid/view/KeyEvent;)Z

    .line 20
    .line 21
    .line 22
    move-result p1

    .line 23
    return p1
.end method

.method protected onPause()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Activity;->onPause()V

    .line 2
    .line 3
    .line 4
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 5
    .line 6
    if-eqz v0, :cond_0

    .line 7
    .line 8
    invoke-virtual {v0}, Landroid/webkit/WebView;->onPause()V

    .line 9
    .line 10
    .line 11
    :cond_0
    return-void
.end method

.method protected onResume()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Activity;->onResume()V

    .line 2
    .line 3
    .line 4
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 5
    .line 6
    if-eqz v0, :cond_0

    .line 7
    .line 8
    invoke-virtual {v0}, Landroid/webkit/WebView;->onResume()V

    .line 9
    .line 10
    .line 11
    :cond_0
    return-void
.end method

.method protected onSaveInstanceState(Landroid/os/Bundle;)V
    .locals 1

    .line 1
    invoke-super {p0, p1}, Landroid/app/Activity;->onSaveInstanceState(Landroid/os/Bundle;)V

    .line 2
    .line 3
    .line 4
    iget-object v0, p0, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->c:Landroid/webkit/WebView;

    .line 5
    .line 6
    if-eqz v0, :cond_0

    .line 7
    .line 8
    invoke-virtual {v0, p1}, Landroid/webkit/WebView;->saveState(Landroid/os/Bundle;)Landroid/webkit/WebBackForwardList;

    .line 9
    .line 10
    .line 11
    :cond_0
    return-void
.end method
