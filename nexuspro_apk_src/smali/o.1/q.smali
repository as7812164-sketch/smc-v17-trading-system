.class public Lo/q;
.super Ljava/lang/Object;
.source "SourceFile"


# instance fields
.field private final a:Landroid/net/Uri;

.field private final b:Ln/d$e;

.field private c:Ljava/util/List;

.field private d:Landroid/os/Bundle;

.field private e:Lp/a;

.field private f:Lp/b;

.field private g:Lo/a;

.field private h:Landroid/net/Uri;

.field private i:I

.field private j:Lo/o;

.field private k:I


# direct methods
.method public constructor <init>(Landroid/net/Uri;)V
    .locals 2

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 2
    .line 3
    .line 4
    new-instance v0, Ln/d$e;

    .line 5
    .line 6
    invoke-direct {v0}, Ln/d$e;-><init>()V

    .line 7
    .line 8
    .line 9
    iput-object v0, p0, Lo/q;->b:Ln/d$e;

    .line 10
    .line 11
    const/4 v0, 0x0

    .line 12
    iput v0, p0, Lo/q;->i:I

    .line 13
    .line 14
    new-instance v1, Lo/o$b;

    .line 15
    .line 16
    invoke-direct {v1}, Lo/o$b;-><init>()V

    .line 17
    .line 18
    .line 19
    iput-object v1, p0, Lo/q;->j:Lo/o;

    .line 20
    .line 21
    iput v0, p0, Lo/q;->k:I

    .line 22
    .line 23
    iput-object p1, p0, Lo/q;->a:Landroid/net/Uri;

    .line 24
    .line 25
    return-void
.end method


# virtual methods
.method public a(Ln/f;)Lo/p;
    .locals 4

    .line 1
    if-eqz p1, :cond_5

    .line 2
    .line 3
    iget-object v0, p0, Lo/q;->b:Ln/d$e;

    .line 4
    .line 5
    invoke-virtual {v0, p1}, Ln/d$e;->h(Ln/f;)Ln/d$e;

    .line 6
    .line 7
    .line 8
    iget-object p1, p0, Lo/q;->b:Ln/d$e;

    .line 9
    .line 10
    invoke-virtual {p1}, Ln/d$e;->a()Ln/d;

    .line 11
    .line 12
    .line 13
    move-result-object p1

    .line 14
    iget-object p1, p1, Ln/d;->a:Landroid/content/Intent;

    .line 15
    .line 16
    iget-object v0, p0, Lo/q;->a:Landroid/net/Uri;

    .line 17
    .line 18
    invoke-virtual {p1, v0}, Landroid/content/Intent;->setData(Landroid/net/Uri;)Landroid/content/Intent;

    .line 19
    .line 20
    .line 21
    const-string v0, "android.support.customtabs.extra.LAUNCH_AS_TRUSTED_WEB_ACTIVITY"

    .line 22
    .line 23
    const/4 v1, 0x1

    .line 24
    invoke-virtual {p1, v0, v1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Z)Landroid/content/Intent;

    .line 25
    .line 26
    .line 27
    iget-object v0, p0, Lo/q;->c:Ljava/util/List;

    .line 28
    .line 29
    if-eqz v0, :cond_0

    .line 30
    .line 31
    new-instance v0, Ljava/util/ArrayList;

    .line 32
    .line 33
    iget-object v1, p0, Lo/q;->c:Ljava/util/List;

    .line 34
    .line 35
    invoke-direct {v0, v1}, Ljava/util/ArrayList;-><init>(Ljava/util/Collection;)V

    .line 36
    .line 37
    .line 38
    const-string v1, "android.support.customtabs.extra.ADDITIONAL_TRUSTED_ORIGINS"

    .line 39
    .line 40
    invoke-virtual {p1, v1, v0}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/io/Serializable;)Landroid/content/Intent;

    .line 41
    .line 42
    .line 43
    :cond_0
    iget-object v0, p0, Lo/q;->d:Landroid/os/Bundle;

    .line 44
    .line 45
    if-eqz v0, :cond_1

    .line 46
    .line 47
    const-string v1, "androidx.browser.trusted.EXTRA_SPLASH_SCREEN_PARAMS"

    .line 48
    .line 49
    invoke-virtual {p1, v1, v0}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Landroid/os/Bundle;)Landroid/content/Intent;

    .line 50
    .line 51
    .line 52
    :cond_1
    sget-object v0, Ljava/util/Collections;->EMPTY_LIST:Ljava/util/List;

    .line 53
    .line 54
    iget-object v1, p0, Lo/q;->f:Lp/b;

    .line 55
    .line 56
    if-eqz v1, :cond_2

    .line 57
    .line 58
    iget-object v2, p0, Lo/q;->e:Lp/a;

    .line 59
    .line 60
    if-eqz v2, :cond_2

    .line 61
    .line 62
    const-string v2, "androidx.browser.trusted.extra.SHARE_TARGET"

    .line 63
    .line 64
    invoke-virtual {v1}, Lp/b;->a()Landroid/os/Bundle;

    .line 65
    .line 66
    .line 67
    move-result-object v1

    .line 68
    invoke-virtual {p1, v2, v1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Landroid/os/Bundle;)Landroid/content/Intent;

    .line 69
    .line 70
    .line 71
    iget-object v1, p0, Lo/q;->e:Lp/a;

    .line 72
    .line 73
    invoke-virtual {v1}, Lp/a;->a()Landroid/os/Bundle;

    .line 74
    .line 75
    .line 76
    move-result-object v1

    .line 77
    const-string v2, "androidx.browser.trusted.extra.SHARE_DATA"

    .line 78
    .line 79
    invoke-virtual {p1, v2, v1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Landroid/os/Bundle;)Landroid/content/Intent;

    .line 80
    .line 81
    .line 82
    iget-object v1, p0, Lo/q;->e:Lp/a;

    .line 83
    .line 84
    iget-object v1, v1, Lp/a;->c:Ljava/util/List;

    .line 85
    .line 86
    if-eqz v1, :cond_2

    .line 87
    .line 88
    goto :goto_0

    .line 89
    :cond_2
    move-object v1, v0

    .line 90
    :goto_0
    iget-object v2, p0, Lo/q;->g:Lo/a;

    .line 91
    .line 92
    if-eqz v2, :cond_3

    .line 93
    .line 94
    const-string v3, "androidx.browser.trusted.extra.FILE_HANDLING_DATA"

    .line 95
    .line 96
    invoke-virtual {v2}, Lo/a;->b()Landroid/os/Bundle;

    .line 97
    .line 98
    .line 99
    move-result-object v2

    .line 100
    invoke-virtual {p1, v3, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Landroid/os/Bundle;)Landroid/content/Intent;

    .line 101
    .line 102
    .line 103
    iget-object v2, p0, Lo/q;->g:Lo/a;

    .line 104
    .line 105
    iget-object v2, v2, Lo/a;->a:Ljava/util/List;

    .line 106
    .line 107
    if-eqz v2, :cond_3

    .line 108
    .line 109
    move-object v0, v2

    .line 110
    :cond_3
    iget-object v2, p0, Lo/q;->j:Lo/o;

    .line 111
    .line 112
    invoke-interface {v2}, Lo/o;->a()Landroid/os/Bundle;

    .line 113
    .line 114
    .line 115
    move-result-object v2

    .line 116
    const-string v3, "androidx.browser.trusted.extra.DISPLAY_MODE"

    .line 117
    .line 118
    invoke-virtual {p1, v3, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Landroid/os/Bundle;)Landroid/content/Intent;

    .line 119
    .line 120
    .line 121
    const-string v2, "androidx.browser.trusted.extra.SCREEN_ORIENTATION"

    .line 122
    .line 123
    iget v3, p0, Lo/q;->k:I

    .line 124
    .line 125
    invoke-virtual {p1, v2, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    .line 126
    .line 127
    .line 128
    iget-object v2, p0, Lo/q;->h:Landroid/net/Uri;

    .line 129
    .line 130
    if-eqz v2, :cond_4

    .line 131
    .line 132
    const-string v3, "androidx.browser.trusted.extra.ORIGINAL_LAUNCH_URL"

    .line 133
    .line 134
    invoke-virtual {p1, v3, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Landroid/os/Parcelable;)Landroid/content/Intent;

    .line 135
    .line 136
    .line 137
    :cond_4
    const-string v2, "androidx.browser.trusted.extra.LAUNCH_HANDLER_CLIENT_MODE"

    .line 138
    .line 139
    iget v3, p0, Lo/q;->i:I

    .line 140
    .line 141
    invoke-virtual {p1, v2, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    .line 142
    .line 143
    .line 144
    new-instance v2, Lo/p;

    .line 145
    .line 146
    invoke-direct {v2, p1, v1, v0}, Lo/p;-><init>(Landroid/content/Intent;Ljava/util/List;Ljava/util/List;)V

    .line 147
    .line 148
    .line 149
    return-object v2

    .line 150
    :cond_5
    new-instance p1, Ljava/lang/NullPointerException;

    .line 151
    .line 152
    const-string v0, "CustomTabsSession is required for launching a TWA"

    .line 153
    .line 154
    invoke-direct {p1, v0}, Ljava/lang/NullPointerException;-><init>(Ljava/lang/String;)V

    .line 155
    .line 156
    .line 157
    throw p1
.end method

.method public b()Ln/d;
    .locals 1

    .line 1
    iget-object v0, p0, Lo/q;->b:Ln/d$e;

    .line 2
    .line 3
    invoke-virtual {v0}, Ln/d$e;->a()Ln/d;

    .line 4
    .line 5
    .line 6
    move-result-object v0

    .line 7
    return-object v0
.end method

.method public c()Landroid/net/Uri;
    .locals 1

    .line 1
    iget-object v0, p0, Lo/q;->a:Landroid/net/Uri;

    .line 2
    .line 3
    return-object v0
.end method

.method public d(Ljava/util/List;)Lo/q;
    .locals 0

    .line 1
    iput-object p1, p0, Lo/q;->c:Ljava/util/List;

    .line 2
    .line 3
    return-object p0
.end method

.method public e(I)Lo/q;
    .locals 1

    .line 1
    iget-object v0, p0, Lo/q;->b:Ln/d$e;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Ln/d$e;->c(I)Ln/d$e;

    .line 4
    .line 5
    .line 6
    return-object p0
.end method

.method public f(ILn/a;)Lo/q;
    .locals 1

    .line 1
    iget-object v0, p0, Lo/q;->b:Ln/d$e;

    .line 2
    .line 3
    invoke-virtual {v0, p1, p2}, Ln/d$e;->d(ILn/a;)Ln/d$e;

    .line 4
    .line 5
    .line 6
    return-object p0
.end method

.method public g(Lo/o;)Lo/q;
    .locals 0

    .line 1
    iput-object p1, p0, Lo/q;->j:Lo/o;

    .line 2
    .line 3
    return-object p0
.end method

.method public h(Lo/a;)Lo/q;
    .locals 0

    .line 1
    iput-object p1, p0, Lo/q;->g:Lo/a;

    .line 2
    .line 3
    return-object p0
.end method

.method public i(I)Lo/q;
    .locals 0

    .line 1
    iput p1, p0, Lo/q;->i:I

    .line 2
    .line 3
    return-object p0
.end method

.method public j(I)Lo/q;
    .locals 1

    .line 1
    iget-object v0, p0, Lo/q;->b:Ln/d$e;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Ln/d$e;->f(I)Ln/d$e;

    .line 4
    .line 5
    .line 6
    return-object p0
.end method

.method public k(I)Lo/q;
    .locals 1

    .line 1
    iget-object v0, p0, Lo/q;->b:Ln/d$e;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Ln/d$e;->g(I)Ln/d$e;

    .line 4
    .line 5
    .line 6
    return-object p0
.end method

.method public l(Landroid/net/Uri;)Lo/q;
    .locals 0

    .line 1
    iput-object p1, p0, Lo/q;->h:Landroid/net/Uri;

    .line 2
    .line 3
    return-object p0
.end method

.method public m(I)Lo/q;
    .locals 0

    .line 1
    iput p1, p0, Lo/q;->k:I

    .line 2
    .line 3
    return-object p0
.end method

.method public n(Lp/b;Lp/a;)Lo/q;
    .locals 0

    .line 1
    iput-object p1, p0, Lo/q;->f:Lp/b;

    .line 2
    .line 3
    iput-object p2, p0, Lo/q;->e:Lp/a;

    .line 4
    .line 5
    return-object p0
.end method

.method public o(Landroid/os/Bundle;)Lo/q;
    .locals 0

    .line 1
    iput-object p1, p0, Lo/q;->d:Landroid/os/Bundle;

    .line 2
    .line 3
    return-object p0
.end method

.method public p(I)Lo/q;
    .locals 1

    .line 1
    iget-object v0, p0, Lo/q;->b:Ln/d$e;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Ln/d$e;->k(I)Ln/d$e;

    .line 4
    .line 5
    .line 6
    return-object p0
.end method
