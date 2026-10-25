.class public abstract LK/h;
.super Landroid/app/Activity;
.source "SourceFile"


# static fields
.field private static f:Z

.field private static g:I


# instance fields
.field private a:LK/i;

.field private b:Z

.field private c:LL/c;

.field private d:LK/I;

.field private e:J


# direct methods
.method public constructor <init>()V
    .locals 0

    .line 1
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method public static synthetic a(LK/h;)V
    .locals 1

    .line 1
    const/4 v0, 0x1

    .line 2
    iput-boolean v0, p0, LK/h;->b:Z

    .line 3
    .line 4
    return-void
.end method

.method private b(Lo/q;)V
    .locals 5

    .line 1
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    const-string v1, "androidx.browser.trusted.extra.FILE_HANDLING_DATA"

    .line 6
    .line 7
    invoke-virtual {v0, v1}, Landroid/content/Intent;->hasExtra(Ljava/lang/String;)Z

    .line 8
    .line 9
    .line 10
    move-result v0

    .line 11
    if-eqz v0, :cond_1

    .line 12
    .line 13
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 14
    .line 15
    .line 16
    move-result-object v0

    .line 17
    invoke-virtual {v0, v1}, Landroid/content/Intent;->getBundleExtra(Ljava/lang/String;)Landroid/os/Bundle;

    .line 18
    .line 19
    .line 20
    move-result-object v0

    .line 21
    if-nez v0, :cond_0

    .line 22
    .line 23
    goto :goto_1

    .line 24
    :cond_0
    invoke-static {v0}, Lo/a;->a(Landroid/os/Bundle;)Lo/a;

    .line 25
    .line 26
    .line 27
    move-result-object v0

    .line 28
    iget-object v0, v0, Lo/a;->a:Ljava/util/List;

    .line 29
    .line 30
    goto :goto_0

    .line 31
    :cond_1
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 32
    .line 33
    .line 34
    move-result-object v0

    .line 35
    invoke-virtual {v0}, Landroid/content/Intent;->getData()Landroid/net/Uri;

    .line 36
    .line 37
    .line 38
    move-result-object v0

    .line 39
    filled-new-array {v0}, [Landroid/net/Uri;

    .line 40
    .line 41
    .line 42
    move-result-object v0

    .line 43
    invoke-static {v0}, Ljava/util/Arrays;->asList([Ljava/lang/Object;)Ljava/util/List;

    .line 44
    .line 45
    .line 46
    move-result-object v0

    .line 47
    :goto_0
    invoke-interface {v0}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    .line 48
    .line 49
    .line 50
    move-result-object v1

    .line 51
    :cond_2
    invoke-interface {v1}, Ljava/util/Iterator;->hasNext()Z

    .line 52
    .line 53
    .line 54
    move-result v2

    .line 55
    if-eqz v2, :cond_5

    .line 56
    .line 57
    invoke-interface {v1}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    .line 58
    .line 59
    .line 60
    move-result-object v2

    .line 61
    check-cast v2, Landroid/net/Uri;

    .line 62
    .line 63
    if-eqz v2, :cond_4

    .line 64
    .line 65
    const-string v3, "content"

    .line 66
    .line 67
    invoke-virtual {v2}, Landroid/net/Uri;->getScheme()Ljava/lang/String;

    .line 68
    .line 69
    .line 70
    move-result-object v4

    .line 71
    invoke-virtual {v3, v4}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 72
    .line 73
    .line 74
    move-result v3

    .line 75
    if-nez v3, :cond_3

    .line 76
    .line 77
    goto :goto_1

    .line 78
    :cond_3
    const/4 v3, 0x3

    .line 79
    invoke-virtual {p0, v2, v3}, Landroid/content/Context;->checkCallingOrSelfUriPermission(Landroid/net/Uri;I)I

    .line 80
    .line 81
    .line 82
    move-result v3

    .line 83
    if-eqz v3, :cond_2

    .line 84
    .line 85
    new-instance p1, Ljava/lang/StringBuilder;

    .line 86
    .line 87
    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    .line 88
    .line 89
    .line 90
    const-string v0, "Failed to open a file - no read / write permissions: "

    .line 91
    .line 92
    invoke-virtual {p1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 93
    .line 94
    .line 95
    invoke-virtual {p1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    .line 96
    .line 97
    .line 98
    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 99
    .line 100
    .line 101
    move-result-object p1

    .line 102
    const-string v0, "TWALauncherActivity"

    .line 103
    .line 104
    invoke-static {v0, p1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 105
    .line 106
    .line 107
    :cond_4
    :goto_1
    return-void

    .line 108
    :cond_5
    new-instance v1, Lo/a;

    .line 109
    .line 110
    invoke-direct {v1, v0}, Lo/a;-><init>(Ljava/util/List;)V

    .line 111
    .line 112
    .line 113
    invoke-virtual {p1, v1}, Lo/q;->h(Lo/a;)Lo/q;

    .line 114
    .line 115
    .line 116
    return-void
.end method

.method private c(Lo/q;)V
    .locals 3

    .line 1
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    invoke-static {v0}, LK/C;->e(Landroid/content/Intent;)Lp/a;

    .line 6
    .line 7
    .line 8
    move-result-object v0

    .line 9
    if-nez v0, :cond_0

    .line 10
    .line 11
    goto :goto_0

    .line 12
    :cond_0
    iget-object v1, p0, LK/h;->a:LK/i;

    .line 13
    .line 14
    iget-object v1, v1, LK/i;->p:Ljava/lang/String;

    .line 15
    .line 16
    const-string v2, "TWALauncherActivity"

    .line 17
    .line 18
    if-nez v1, :cond_1

    .line 19
    .line 20
    const-string p1, "Failed to share: share target not defined in the AndroidManifest"

    .line 21
    .line 22
    invoke-static {v2, p1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 23
    .line 24
    .line 25
    return-void

    .line 26
    :cond_1
    :try_start_0
    invoke-static {v1}, LK/C;->d(Ljava/lang/String;)Lp/b;

    .line 27
    .line 28
    .line 29
    move-result-object v1

    .line 30
    invoke-virtual {p1, v1, v0}, Lo/q;->n(Lp/b;Lp/a;)Lo/q;
    :try_end_0
    .catch Lorg/json/JSONException; {:try_start_0 .. :try_end_0} :catch_0

    .line 31
    .line 32
    .line 33
    return-void

    .line 34
    :catch_0
    move-exception p1

    .line 35
    new-instance v0, Ljava/lang/StringBuilder;

    .line 36
    .line 37
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    .line 38
    .line 39
    .line 40
    const-string v1, "Failed to parse share target json: "

    .line 41
    .line 42
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 43
    .line 44
    .line 45
    invoke-virtual {p1}, Ljava/lang/Object;->toString()Ljava/lang/String;

    .line 46
    .line 47
    .line 48
    move-result-object p1

    .line 49
    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 50
    .line 51
    .line 52
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 53
    .line 54
    .line 55
    move-result-object p1

    .line 56
    invoke-static {v2, p1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 57
    .line 58
    .line 59
    :goto_0
    return-void
.end method

.method private e(I)I
    .locals 0

    .line 1
    invoke-static {p0, p1}, Landroidx/core/content/a;->a(Landroid/content/Context;I)I

    .line 2
    .line 3
    .line 4
    move-result p1

    .line 5
    return p1
.end method

.method private n()Z
    .locals 6

    .line 1
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    invoke-virtual {v0}, Landroid/content/Intent;->getFlags()I

    .line 6
    .line 7
    .line 8
    move-result v0

    .line 9
    const/high16 v1, 0x10000000

    .line 10
    .line 11
    and-int/2addr v0, v1

    .line 12
    const/4 v2, 0x0

    .line 13
    const/4 v3, 0x1

    .line 14
    if-eqz v0, :cond_0

    .line 15
    .line 16
    move v0, v3

    .line 17
    goto :goto_0

    .line 18
    :cond_0
    move v0, v2

    .line 19
    :goto_0
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 20
    .line 21
    .line 22
    move-result-object v4

    .line 23
    invoke-virtual {v4}, Landroid/content/Intent;->getFlags()I

    .line 24
    .line 25
    .line 26
    move-result v4

    .line 27
    const/high16 v5, 0x80000

    .line 28
    .line 29
    and-int/2addr v4, v5

    .line 30
    if-eqz v4, :cond_1

    .line 31
    .line 32
    move v4, v3

    .line 33
    goto :goto_1

    .line 34
    :cond_1
    move v4, v2

    .line 35
    :goto_1
    if-eqz v0, :cond_2

    .line 36
    .line 37
    if-nez v4, :cond_2

    .line 38
    .line 39
    return v2

    .line 40
    :cond_2
    new-instance v0, Landroid/content/Intent;

    .line 41
    .line 42
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 43
    .line 44
    .line 45
    move-result-object v2

    .line 46
    invoke-direct {v0, v2}, Landroid/content/Intent;-><init>(Landroid/content/Intent;)V

    .line 47
    .line 48
    .line 49
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 50
    .line 51
    .line 52
    move-result-object v2

    .line 53
    invoke-virtual {v2}, Landroid/content/Intent;->getFlags()I

    .line 54
    .line 55
    .line 56
    move-result v2

    .line 57
    or-int/2addr v1, v2

    .line 58
    const v2, -0x80001

    .line 59
    .line 60
    .line 61
    and-int/2addr v1, v2

    .line 62
    invoke-virtual {v0, v1}, Landroid/content/Intent;->setFlags(I)Landroid/content/Intent;

    .line 63
    .line 64
    .line 65
    invoke-virtual {p0, v0}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V

    .line 66
    .line 67
    .line 68
    return v3
.end method

.method private p()Z
    .locals 1

    .line 1
    iget-object v0, p0, LK/h;->a:LK/i;

    .line 2
    .line 3
    iget v0, v0, LK/i;->h:I

    .line 4
    .line 5
    if-nez v0, :cond_0

    .line 6
    .line 7
    const/4 v0, 0x0

    .line 8
    return v0

    .line 9
    :cond_0
    invoke-virtual {p0}, Landroid/app/Activity;->isTaskRoot()Z

    .line 10
    .line 11
    .line 12
    move-result v0

    .line 13
    return v0
.end method


# virtual methods
.method protected d()LK/I;
    .locals 4

    .line 1
    new-instance v0, LK/I;

    .line 2
    .line 3
    invoke-virtual {p0}, Landroid/app/Activity;->getTaskId()I

    .line 4
    .line 5
    .line 6
    move-result v1

    .line 7
    invoke-static {v1}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    .line 8
    .line 9
    .line 10
    move-result-object v1

    .line 11
    invoke-static {v1}, LK/A;->a(Ljava/lang/Integer;)Ljava/lang/Integer;

    .line 12
    .line 13
    .line 14
    move-result-object v1

    .line 15
    new-instance v2, LK/B;

    .line 16
    .line 17
    invoke-direct {v2, p0}, LK/B;-><init>(Landroid/content/Context;)V

    .line 18
    .line 19
    .line 20
    const/4 v3, 0x0

    .line 21
    invoke-direct {v0, p0, v3, v1, v2}, LK/I;-><init>(Landroid/content/Context;Ljava/lang/String;Ljava/lang/Integer;Lo/m;)V

    .line 22
    .line 23
    .line 24
    return-object v0
.end method

.method protected f()Ln/b;
    .locals 1

    .line 1
    new-instance v0, LK/z;

    .line 2
    .line 3
    invoke-direct {v0}, LK/z;-><init>()V

    .line 4
    .line 5
    .line 6
    return-object v0
.end method

.method protected g()Lo/o;
    .locals 1

    .line 1
    iget-object v0, p0, LK/h;->a:LK/i;

    .line 2
    .line 3
    iget-object v0, v0, LK/i;->n:Lo/o;

    .line 4
    .line 5
    return-object v0
.end method

.method protected h()LK/I$a;
    .locals 2

    .line 1
    iget-object v0, p0, LK/h;->a:LK/i;

    .line 2
    .line 3
    iget-object v0, v0, LK/i;->m:Ljava/lang/String;

    .line 4
    .line 5
    const-string v1, "webview"

    .line 6
    .line 7
    invoke-virtual {v1, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    .line 8
    .line 9
    .line 10
    move-result v0

    .line 11
    if-eqz v0, :cond_0

    .line 12
    .line 13
    sget-object v0, LK/I;->k:LK/I$a;

    .line 14
    .line 15
    return-object v0

    .line 16
    :cond_0
    sget-object v0, LK/I;->j:LK/I$a;

    .line 17
    .line 18
    return-object v0
.end method

.method protected i()Landroid/net/Uri;
    .locals 6

    .line 1
    iget-object v0, p0, LK/h;->a:LK/i;

    .line 2
    .line 3
    iget-object v0, v0, LK/i;->a:Ljava/lang/String;

    .line 4
    .line 5
    invoke-static {v0}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    .line 6
    .line 7
    .line 8
    move-result-object v0

    .line 9
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 10
    .line 11
    .line 12
    move-result-object v1

    .line 13
    invoke-virtual {v1}, Landroid/content/Intent;->getData()Landroid/net/Uri;

    .line 14
    .line 15
    .line 16
    move-result-object v1

    .line 17
    const-string v2, "TWALauncherActivity"

    .line 18
    .line 19
    if-eqz v1, :cond_4

    .line 20
    .line 21
    invoke-virtual {p0}, LK/h;->j()Ljava/util/Map;

    .line 22
    .line 23
    .line 24
    move-result-object v3

    .line 25
    invoke-virtual {v1}, Landroid/net/Uri;->getScheme()Ljava/lang/String;

    .line 26
    .line 27
    .line 28
    move-result-object v4

    .line 29
    const-string v5, "https"

    .line 30
    .line 31
    invoke-virtual {v5, v4}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 32
    .line 33
    .line 34
    move-result v5

    .line 35
    if-eqz v5, :cond_0

    .line 36
    .line 37
    new-instance v0, Ljava/lang/StringBuilder;

    .line 38
    .line 39
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    .line 40
    .line 41
    .line 42
    const-string v3, "Using url from Intent: "

    .line 43
    .line 44
    invoke-virtual {v0, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 45
    .line 46
    .line 47
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    .line 48
    .line 49
    .line 50
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 51
    .line 52
    .line 53
    move-result-object v0

    .line 54
    invoke-static {v2, v0}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 55
    .line 56
    .line 57
    return-object v1

    .line 58
    :cond_0
    const-string v5, "content"

    .line 59
    .line 60
    invoke-virtual {v5, v4}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 61
    .line 62
    .line 63
    move-result v5

    .line 64
    if-eqz v5, :cond_2

    .line 65
    .line 66
    iget-object v1, p0, LK/h;->a:LK/i;

    .line 67
    .line 68
    iget-object v1, v1, LK/i;->q:Ljava/lang/String;

    .line 69
    .line 70
    if-nez v1, :cond_1

    .line 71
    .line 72
    return-object v0

    .line 73
    :cond_1
    invoke-static {v1}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    .line 74
    .line 75
    .line 76
    move-result-object v0

    .line 77
    return-object v0

    .line 78
    :cond_2
    invoke-interface {v3, v4}, Ljava/util/Map;->get(Ljava/lang/Object;)Ljava/lang/Object;

    .line 79
    .line 80
    .line 81
    move-result-object v3

    .line 82
    check-cast v3, Landroid/net/Uri;

    .line 83
    .line 84
    if-eqz v3, :cond_3

    .line 85
    .line 86
    invoke-virtual {v1}, Landroid/net/Uri;->toString()Ljava/lang/String;

    .line 87
    .line 88
    .line 89
    move-result-object v0

    .line 90
    invoke-static {v0}, Landroid/net/Uri;->encode(Ljava/lang/String;)Ljava/lang/String;

    .line 91
    .line 92
    .line 93
    move-result-object v0

    .line 94
    invoke-virtual {v3}, Landroid/net/Uri;->toString()Ljava/lang/String;

    .line 95
    .line 96
    .line 97
    move-result-object v1

    .line 98
    filled-new-array {v0}, [Ljava/lang/Object;

    .line 99
    .line 100
    .line 101
    move-result-object v0

    .line 102
    invoke-static {v1, v0}, Ljava/lang/String;->format(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    .line 103
    .line 104
    .line 105
    move-result-object v0

    .line 106
    invoke-static {v0}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    .line 107
    .line 108
    .line 109
    move-result-object v0

    .line 110
    new-instance v1, Ljava/lang/StringBuilder;

    .line 111
    .line 112
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    .line 113
    .line 114
    .line 115
    const-string v3, "Using protocol handler url: "

    .line 116
    .line 117
    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 118
    .line 119
    .line 120
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    .line 121
    .line 122
    .line 123
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 124
    .line 125
    .line 126
    move-result-object v1

    .line 127
    invoke-static {v2, v1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 128
    .line 129
    .line 130
    return-object v0

    .line 131
    :cond_3
    new-instance v1, Ljava/lang/StringBuilder;

    .line 132
    .line 133
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    .line 134
    .line 135
    .line 136
    const-string v3, "Scheme "

    .line 137
    .line 138
    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 139
    .line 140
    .line 141
    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 142
    .line 143
    .line 144
    const-string v3, " was registered in the manifest but not in getProtocolHandlers()! Ignoring it and falling back to the default url."

    .line 145
    .line 146
    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 147
    .line 148
    .line 149
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 150
    .line 151
    .line 152
    move-result-object v1

    .line 153
    invoke-static {v2, v1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 154
    .line 155
    .line 156
    :cond_4
    new-instance v1, Ljava/lang/StringBuilder;

    .line 157
    .line 158
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    .line 159
    .line 160
    .line 161
    const-string v3, "Using url from Manifest: "

    .line 162
    .line 163
    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 164
    .line 165
    .line 166
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    .line 167
    .line 168
    .line 169
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 170
    .line 171
    .line 172
    move-result-object v1

    .line 173
    invoke-static {v2, v1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 174
    .line 175
    .line 176
    return-object v0
.end method

.method protected j()Ljava/util/Map;
    .locals 1

    .line 1
    sget-object v0, Ljava/util/Collections;->EMPTY_MAP:Ljava/util/Map;

    .line 2
    .line 3
    return-object v0
.end method

.method protected k()Landroid/widget/ImageView$ScaleType;
    .locals 1

    .line 1
    sget-object v0, Landroid/widget/ImageView$ScaleType;->CENTER:Landroid/widget/ImageView$ScaleType;

    .line 2
    .line 3
    return-object v0
.end method

.method protected l()Landroid/graphics/Matrix;
    .locals 1

    .line 1
    const/4 v0, 0x0

    .line 2
    return-object v0
.end method

.method protected m()V
    .locals 9

    .line 1
    invoke-virtual {p0}, Landroid/app/Activity;->isFinishing()Z

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    if-eqz v0, :cond_0

    .line 6
    .line 7
    const-string v0, "TWALauncherActivity"

    .line 8
    .line 9
    const-string v1, "Aborting launchTwa() as Activity is finishing"

    .line 10
    .line 11
    invoke-static {v0, v1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 12
    .line 13
    .line 14
    return-void

    .line 15
    :cond_0
    new-instance v0, Ln/a$a;

    .line 16
    .line 17
    invoke-direct {v0}, Ln/a$a;-><init>()V

    .line 18
    .line 19
    .line 20
    iget-object v1, p0, LK/h;->a:LK/i;

    .line 21
    .line 22
    iget v1, v1, LK/i;->c:I

    .line 23
    .line 24
    invoke-direct {p0, v1}, LK/h;->e(I)I

    .line 25
    .line 26
    .line 27
    move-result v1

    .line 28
    invoke-virtual {v0, v1}, Ln/a$a;->d(I)Ln/a$a;

    .line 29
    .line 30
    .line 31
    move-result-object v0

    .line 32
    iget-object v1, p0, LK/h;->a:LK/i;

    .line 33
    .line 34
    iget v1, v1, LK/i;->e:I

    .line 35
    .line 36
    invoke-direct {p0, v1}, LK/h;->e(I)I

    .line 37
    .line 38
    .line 39
    move-result v1

    .line 40
    invoke-virtual {v0, v1}, Ln/a$a;->b(I)Ln/a$a;

    .line 41
    .line 42
    .line 43
    move-result-object v0

    .line 44
    iget-object v1, p0, LK/h;->a:LK/i;

    .line 45
    .line 46
    iget v1, v1, LK/i;->g:I

    .line 47
    .line 48
    invoke-direct {p0, v1}, LK/h;->e(I)I

    .line 49
    .line 50
    .line 51
    move-result v1

    .line 52
    invoke-virtual {v0, v1}, Ln/a$a;->c(I)Ln/a$a;

    .line 53
    .line 54
    .line 55
    move-result-object v0

    .line 56
    invoke-virtual {v0}, Ln/a$a;->a()Ln/a;

    .line 57
    .line 58
    .line 59
    move-result-object v0

    .line 60
    invoke-virtual {p0}, LK/h;->i()Landroid/net/Uri;

    .line 61
    .line 62
    .line 63
    move-result-object v1

    .line 64
    new-instance v2, Lo/q;

    .line 65
    .line 66
    invoke-direct {v2, v1}, Lo/q;-><init>(Landroid/net/Uri;)V

    .line 67
    .line 68
    .line 69
    iget-object v3, p0, LK/h;->a:LK/i;

    .line 70
    .line 71
    iget v3, v3, LK/i;->b:I

    .line 72
    .line 73
    invoke-direct {p0, v3}, LK/h;->e(I)I

    .line 74
    .line 75
    .line 76
    move-result v3

    .line 77
    invoke-virtual {v2, v3}, Lo/q;->p(I)Lo/q;

    .line 78
    .line 79
    .line 80
    move-result-object v2

    .line 81
    iget-object v3, p0, LK/h;->a:LK/i;

    .line 82
    .line 83
    iget v3, v3, LK/i;->d:I

    .line 84
    .line 85
    invoke-direct {p0, v3}, LK/h;->e(I)I

    .line 86
    .line 87
    .line 88
    move-result v3

    .line 89
    invoke-virtual {v2, v3}, Lo/q;->j(I)Lo/q;

    .line 90
    .line 91
    .line 92
    move-result-object v2

    .line 93
    iget-object v3, p0, LK/h;->a:LK/i;

    .line 94
    .line 95
    iget v3, v3, LK/i;->f:I

    .line 96
    .line 97
    invoke-direct {p0, v3}, LK/h;->e(I)I

    .line 98
    .line 99
    .line 100
    move-result v3

    .line 101
    invoke-virtual {v2, v3}, Lo/q;->k(I)Lo/q;

    .line 102
    .line 103
    .line 104
    move-result-object v2

    .line 105
    const/4 v3, 0x0

    .line 106
    invoke-virtual {v2, v3}, Lo/q;->e(I)Lo/q;

    .line 107
    .line 108
    .line 109
    move-result-object v2

    .line 110
    const/4 v3, 0x2

    .line 111
    invoke-virtual {v2, v3, v0}, Lo/q;->f(ILn/a;)Lo/q;

    .line 112
    .line 113
    .line 114
    move-result-object v0

    .line 115
    invoke-virtual {p0}, LK/h;->g()Lo/o;

    .line 116
    .line 117
    .line 118
    move-result-object v2

    .line 119
    invoke-virtual {v0, v2}, Lo/q;->g(Lo/o;)Lo/q;

    .line 120
    .line 121
    .line 122
    move-result-object v0

    .line 123
    iget-object v2, p0, LK/h;->a:LK/i;

    .line 124
    .line 125
    iget v2, v2, LK/i;->o:I

    .line 126
    .line 127
    invoke-virtual {v0, v2}, Lo/q;->m(I)Lo/q;

    .line 128
    .line 129
    .line 130
    move-result-object v0

    .line 131
    iget-object v2, p0, LK/h;->a:LK/i;

    .line 132
    .line 133
    iget v2, v2, LK/i;->r:I

    .line 134
    .line 135
    invoke-virtual {v0, v2}, Lo/q;->i(I)Lo/q;

    .line 136
    .line 137
    .line 138
    move-result-object v4

    .line 139
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 140
    .line 141
    .line 142
    move-result-object v0

    .line 143
    invoke-virtual {v0}, Landroid/content/Intent;->getData()Landroid/net/Uri;

    .line 144
    .line 145
    .line 146
    move-result-object v0

    .line 147
    invoke-virtual {v1, v0}, Landroid/net/Uri;->equals(Ljava/lang/Object;)Z

    .line 148
    .line 149
    .line 150
    move-result v1

    .line 151
    if-nez v1, :cond_1

    .line 152
    .line 153
    invoke-virtual {v4, v0}, Lo/q;->l(Landroid/net/Uri;)Lo/q;

    .line 154
    .line 155
    .line 156
    :cond_1
    iget-object v0, p0, LK/h;->a:LK/i;

    .line 157
    .line 158
    iget-object v0, v0, LK/i;->l:Ljava/util/List;

    .line 159
    .line 160
    if-eqz v0, :cond_2

    .line 161
    .line 162
    invoke-virtual {v4, v0}, Lo/q;->d(Ljava/util/List;)Lo/q;

    .line 163
    .line 164
    .line 165
    :cond_2
    invoke-direct {p0, v4}, LK/h;->c(Lo/q;)V

    .line 166
    .line 167
    .line 168
    invoke-direct {p0, v4}, LK/h;->b(Lo/q;)V

    .line 169
    .line 170
    .line 171
    invoke-virtual {p0}, LK/h;->d()LK/I;

    .line 172
    .line 173
    .line 174
    move-result-object v0

    .line 175
    iput-object v0, p0, LK/h;->d:LK/I;

    .line 176
    .line 177
    iget-wide v1, p0, LK/h;->e:J

    .line 178
    .line 179
    invoke-virtual {v0, v1, v2}, LK/I;->q(J)V

    .line 180
    .line 181
    .line 182
    iget-object v3, p0, LK/h;->d:LK/I;

    .line 183
    .line 184
    invoke-virtual {p0}, LK/h;->f()Ln/b;

    .line 185
    .line 186
    .line 187
    move-result-object v5

    .line 188
    iget-object v6, p0, LK/h;->c:LL/c;

    .line 189
    .line 190
    new-instance v7, LK/g;

    .line 191
    .line 192
    invoke-direct {v7, p0}, LK/g;-><init>(LK/h;)V

    .line 193
    .line 194
    .line 195
    invoke-virtual {p0}, LK/h;->h()LK/I$a;

    .line 196
    .line 197
    .line 198
    move-result-object v8

    .line 199
    invoke-virtual/range {v3 .. v8}, LK/I;->m(Lo/q;Ln/b;LL/e;Ljava/lang/Runnable;LK/I$a;)V

    .line 200
    .line 201
    .line 202
    sget-boolean v0, LK/h;->f:Z

    .line 203
    .line 204
    if-nez v0, :cond_3

    .line 205
    .line 206
    iget-object v0, p0, LK/h;->d:LK/I;

    .line 207
    .line 208
    invoke-virtual {v0}, LK/I;->l()Ljava/lang/String;

    .line 209
    .line 210
    .line 211
    move-result-object v0

    .line 212
    invoke-static {p0, v0}, LK/d;->b(Landroid/content/Context;Ljava/lang/String;)V

    .line 213
    .line 214
    .line 215
    const/4 v0, 0x1

    .line 216
    sput-boolean v0, LK/h;->f:Z

    .line 217
    .line 218
    :cond_3
    invoke-virtual {p0}, Landroid/content/Context;->getApplicationContext()Landroid/content/Context;

    .line 219
    .line 220
    .line 221
    move-result-object v0

    .line 222
    invoke-virtual {v0}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 223
    .line 224
    .line 225
    move-result-object v0

    .line 226
    invoke-static {v0}, LK/c;->a(Landroid/content/pm/PackageManager;)Z

    .line 227
    .line 228
    .line 229
    move-result v0

    .line 230
    if-eqz v0, :cond_4

    .line 231
    .line 232
    new-instance v0, LK/K;

    .line 233
    .line 234
    invoke-direct {v0, p0}, LK/K;-><init>(Landroid/content/Context;)V

    .line 235
    .line 236
    .line 237
    const-string v1, "org.chromium.arc.payment_app"

    .line 238
    .line 239
    invoke-virtual {v0, v1}, LK/K;->b(Ljava/lang/String;)V

    .line 240
    .line 241
    .line 242
    goto :goto_0

    .line 243
    :cond_4
    new-instance v0, LK/K;

    .line 244
    .line 245
    invoke-direct {v0, p0}, LK/K;-><init>(Landroid/content/Context;)V

    .line 246
    .line 247
    .line 248
    iget-object v1, p0, LK/h;->d:LK/I;

    .line 249
    .line 250
    invoke-virtual {v1}, LK/I;->l()Ljava/lang/String;

    .line 251
    .line 252
    .line 253
    move-result-object v1

    .line 254
    invoke-virtual {v0, v1}, LK/K;->b(Ljava/lang/String;)V

    .line 255
    .line 256
    .line 257
    :goto_0
    iget-object v0, p0, LK/h;->d:LK/I;

    .line 258
    .line 259
    invoke-virtual {v0}, LK/I;->l()Ljava/lang/String;

    .line 260
    .line 261
    .line 262
    move-result-object v0

    .line 263
    invoke-static {p0, v0}, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity;->b(Landroid/content/Context;Ljava/lang/String;)V

    .line 264
    .line 265
    .line 266
    return-void
.end method

.method protected o()Z
    .locals 1

    .line 1
    const/4 v0, 0x1

    .line 2
    return v0
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .locals 9

    .line 1
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    .line 2
    .line 3
    .line 4
    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    .line 5
    .line 6
    .line 7
    move-result-wide v0

    .line 8
    iput-wide v0, p0, LK/h;->e:J

    .line 9
    .line 10
    sget v0, LK/h;->g:I

    .line 11
    .line 12
    const/4 v1, 0x1

    .line 13
    add-int/2addr v0, v1

    .line 14
    sput v0, LK/h;->g:I

    .line 15
    .line 16
    const/4 v2, 0x0

    .line 17
    if-le v0, v1, :cond_0

    .line 18
    .line 19
    move v0, v1

    .line 20
    goto :goto_0

    .line 21
    :cond_0
    move v0, v2

    .line 22
    :goto_0
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 23
    .line 24
    .line 25
    move-result-object v3

    .line 26
    invoke-virtual {v3}, Landroid/content/Intent;->getData()Landroid/net/Uri;

    .line 27
    .line 28
    .line 29
    move-result-object v3

    .line 30
    if-eqz v3, :cond_1

    .line 31
    .line 32
    goto :goto_1

    .line 33
    :cond_1
    move v1, v2

    .line 34
    :goto_1
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;

    .line 35
    .line 36
    .line 37
    move-result-object v2

    .line 38
    invoke-static {v2}, LK/C;->a(Landroid/content/Intent;)Z

    .line 39
    .line 40
    .line 41
    move-result v2

    .line 42
    if-eqz v0, :cond_2

    .line 43
    .line 44
    if-nez v1, :cond_2

    .line 45
    .line 46
    if-nez v2, :cond_2

    .line 47
    .line 48
    invoke-virtual {p0}, Landroid/app/Activity;->finish()V

    .line 49
    .line 50
    .line 51
    return-void

    .line 52
    :cond_2
    invoke-direct {p0}, LK/h;->n()Z

    .line 53
    .line 54
    .line 55
    move-result v0

    .line 56
    if-eqz v0, :cond_3

    .line 57
    .line 58
    invoke-virtual {p0}, Landroid/app/Activity;->finish()V

    .line 59
    .line 60
    .line 61
    return-void

    .line 62
    :cond_3
    if-eqz p1, :cond_4

    .line 63
    .line 64
    const-string v0, "android.support.customtabs.trusted.BROWSER_WAS_LAUNCHED_KEY"

    .line 65
    .line 66
    invoke-virtual {p1, v0}, Landroid/os/BaseBundle;->getBoolean(Ljava/lang/String;)Z

    .line 67
    .line 68
    .line 69
    move-result p1

    .line 70
    if-eqz p1, :cond_4

    .line 71
    .line 72
    invoke-virtual {p0}, Landroid/app/Activity;->finish()V

    .line 73
    .line 74
    .line 75
    return-void

    .line 76
    :cond_4
    invoke-static {p0}, LK/i;->d(Landroid/content/Context;)LK/i;

    .line 77
    .line 78
    .line 79
    move-result-object p1

    .line 80
    iput-object p1, p0, LK/h;->a:LK/i;

    .line 81
    .line 82
    invoke-direct {p0}, LK/h;->p()Z

    .line 83
    .line 84
    .line 85
    move-result p1

    .line 86
    if-eqz p1, :cond_5

    .line 87
    .line 88
    new-instance v0, LL/c;

    .line 89
    .line 90
    iget-object p1, p0, LK/h;->a:LK/i;

    .line 91
    .line 92
    iget v2, p1, LK/i;->h:I

    .line 93
    .line 94
    iget p1, p1, LK/i;->i:I

    .line 95
    .line 96
    invoke-direct {p0, p1}, LK/h;->e(I)I

    .line 97
    .line 98
    .line 99
    move-result v3

    .line 100
    invoke-virtual {p0}, LK/h;->k()Landroid/widget/ImageView$ScaleType;

    .line 101
    .line 102
    .line 103
    move-result-object v4

    .line 104
    invoke-virtual {p0}, LK/h;->l()Landroid/graphics/Matrix;

    .line 105
    .line 106
    .line 107
    move-result-object v5

    .line 108
    iget-object p1, p0, LK/h;->a:LK/i;

    .line 109
    .line 110
    iget v6, p1, LK/i;->k:I

    .line 111
    .line 112
    iget-object v7, p1, LK/i;->j:Ljava/lang/String;

    .line 113
    .line 114
    iget-boolean v8, p1, LK/i;->s:Z

    .line 115
    .line 116
    move-object v1, p0

    .line 117
    invoke-direct/range {v0 .. v8}, LL/c;-><init>(Landroid/app/Activity;IILandroid/widget/ImageView$ScaleType;Landroid/graphics/Matrix;ILjava/lang/String;Z)V

    .line 118
    .line 119
    .line 120
    iput-object v0, v1, LK/h;->c:LL/c;

    .line 121
    .line 122
    goto :goto_2

    .line 123
    :cond_5
    move-object v1, p0

    .line 124
    :goto_2
    invoke-virtual {p0}, LK/h;->o()Z

    .line 125
    .line 126
    .line 127
    move-result p1

    .line 128
    if-eqz p1, :cond_6

    .line 129
    .line 130
    invoke-virtual {p0}, LK/h;->m()V

    .line 131
    .line 132
    .line 133
    :cond_6
    return-void
.end method

.method protected onDestroy()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Activity;->onDestroy()V

    .line 2
    .line 3
    .line 4
    sget v0, LK/h;->g:I

    .line 5
    .line 6
    add-int/lit8 v0, v0, -0x1

    .line 7
    .line 8
    sput v0, LK/h;->g:I

    .line 9
    .line 10
    iget-object v0, p0, LK/h;->d:LK/I;

    .line 11
    .line 12
    if-eqz v0, :cond_0

    .line 13
    .line 14
    invoke-virtual {v0}, LK/I;->k()V

    .line 15
    .line 16
    .line 17
    :cond_0
    iget-object v0, p0, LK/h;->c:LL/c;

    .line 18
    .line 19
    if-eqz v0, :cond_1

    .line 20
    .line 21
    invoke-virtual {v0}, LL/c;->f()V

    .line 22
    .line 23
    .line 24
    :cond_1
    return-void
.end method

.method public onEnterAnimationComplete()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Activity;->onEnterAnimationComplete()V

    .line 2
    .line 3
    .line 4
    iget-object v0, p0, LK/h;->c:LL/c;

    .line 5
    .line 6
    if-eqz v0, :cond_0

    .line 7
    .line 8
    invoke-virtual {v0}, LL/c;->h()V

    .line 9
    .line 10
    .line 11
    :cond_0
    return-void
.end method

.method protected onRestart()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Activity;->onRestart()V

    .line 2
    .line 3
    .line 4
    iget-boolean v0, p0, LK/h;->b:Z

    .line 5
    .line 6
    if-eqz v0, :cond_0

    .line 7
    .line 8
    invoke-virtual {p0}, Landroid/app/Activity;->finish()V

    .line 9
    .line 10
    .line 11
    :cond_0
    return-void
.end method

.method protected onSaveInstanceState(Landroid/os/Bundle;)V
    .locals 2

    .line 1
    invoke-super {p0, p1}, Landroid/app/Activity;->onSaveInstanceState(Landroid/os/Bundle;)V

    .line 2
    .line 3
    .line 4
    const-string v0, "android.support.customtabs.trusted.BROWSER_WAS_LAUNCHED_KEY"

    .line 5
    .line 6
    iget-boolean v1, p0, LK/h;->b:Z

    .line 7
    .line 8
    invoke-virtual {p1, v0, v1}, Landroid/os/BaseBundle;->putBoolean(Ljava/lang/String;Z)V

    .line 9
    .line 10
    .line 11
    return-void
.end method
