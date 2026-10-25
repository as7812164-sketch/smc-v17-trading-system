.class public LK/i;
.super Ljava/lang/Object;
.source "SourceFile"


# static fields
.field private static final t:Ljava/util/Map;


# instance fields
.field public final a:Ljava/lang/String;

.field public final b:I

.field public final c:I

.field public final d:I

.field public final e:I

.field public final f:I

.field public final g:I

.field public final h:I

.field public final i:I

.field public final j:Ljava/lang/String;

.field public final k:I

.field public final l:Ljava/util/List;

.field public final m:Ljava/lang/String;

.field public final n:Lo/o;

.field public final o:I

.field public final p:Ljava/lang/String;

.field public final q:Ljava/lang/String;

.field public final r:I

.field public final s:Z


# direct methods
.method static constructor <clinit>()V
    .locals 9

    .line 1
    const/4 v0, 0x1

    .line 2
    invoke-static {v0}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    .line 3
    .line 4
    .line 5
    move-result-object v2

    .line 6
    const/4 v0, 0x2

    .line 7
    invoke-static {v0}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    .line 8
    .line 9
    .line 10
    move-result-object v4

    .line 11
    const/4 v0, 0x3

    .line 12
    invoke-static {v0}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    .line 13
    .line 14
    .line 15
    move-result-object v6

    .line 16
    const/4 v0, 0x0

    .line 17
    invoke-static {v0}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    .line 18
    .line 19
    .line 20
    move-result-object v8

    .line 21
    const-string v1, "navigate-existing"

    .line 22
    .line 23
    const-string v3, "focus-existing"

    .line 24
    .line 25
    const-string v5, "navigate-new"

    .line 26
    .line 27
    const-string v7, "auto"

    .line 28
    .line 29
    invoke-static/range {v1 .. v8}, LN/g;->f(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)LN/g;

    .line 30
    .line 31
    .line 32
    move-result-object v0

    .line 33
    sput-object v0, LK/i;->t:Ljava/util/Map;

    .line 34
    .line 35
    return-void
.end method

.method private constructor <init>(Landroid/os/Bundle;Landroid/content/res/Resources;)V
    .locals 4

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 2
    .line 3
    .line 4
    const-string v0, "android.support.customtabs.trusted.DEFAULT_URL"

    .line 5
    .line 6
    invoke-virtual {p1, v0}, Landroid/os/BaseBundle;->getString(Ljava/lang/String;)Ljava/lang/String;

    .line 7
    .line 8
    .line 9
    move-result-object v0

    .line 10
    iput-object v0, p0, LK/i;->a:Ljava/lang/String;

    .line 11
    .line 12
    const-string v0, "android.support.customtabs.trusted.STATUS_BAR_COLOR"

    .line 13
    .line 14
    const v1, 0x106000b

    .line 15
    .line 16
    .line 17
    invoke-virtual {p1, v0, v1}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 18
    .line 19
    .line 20
    move-result v0

    .line 21
    iput v0, p0, LK/i;->b:I

    .line 22
    .line 23
    const-string v2, "android.support.customtabs.trusted.STATUS_BAR_COLOR_DARK"

    .line 24
    .line 25
    invoke-virtual {p1, v2, v0}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 26
    .line 27
    .line 28
    move-result v0

    .line 29
    iput v0, p0, LK/i;->c:I

    .line 30
    .line 31
    const-string v0, "android.support.customtabs.trusted.NAVIGATION_BAR_COLOR"

    .line 32
    .line 33
    invoke-virtual {p1, v0, v1}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 34
    .line 35
    .line 36
    move-result v0

    .line 37
    iput v0, p0, LK/i;->d:I

    .line 38
    .line 39
    const-string v2, "android.support.customtabs.trusted.NAVIGATION_BAR_COLOR_DARK"

    .line 40
    .line 41
    invoke-virtual {p1, v2, v0}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 42
    .line 43
    .line 44
    move-result v2

    .line 45
    iput v2, p0, LK/i;->e:I

    .line 46
    .line 47
    const-string v2, "androix.browser.trusted.NAVIGATION_BAR_DIVIDER_COLOR"

    .line 48
    .line 49
    const v3, 0x106000d

    .line 50
    .line 51
    .line 52
    invoke-virtual {p1, v2, v3}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 53
    .line 54
    .line 55
    move-result v2

    .line 56
    iput v2, p0, LK/i;->f:I

    .line 57
    .line 58
    const-string v2, "androix.browser.trusted.NAVIGATION_BAR_DIVIDER_COLOR_DARK"

    .line 59
    .line 60
    invoke-virtual {p1, v2, v0}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 61
    .line 62
    .line 63
    move-result v0

    .line 64
    iput v0, p0, LK/i;->g:I

    .line 65
    .line 66
    const-string v0, "android.support.customtabs.trusted.SPLASH_IMAGE_DRAWABLE"

    .line 67
    .line 68
    const/4 v2, 0x0

    .line 69
    invoke-virtual {p1, v0, v2}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 70
    .line 71
    .line 72
    move-result v0

    .line 73
    iput v0, p0, LK/i;->h:I

    .line 74
    .line 75
    const-string v0, "android.support.customtabs.trusted.SPLASH_SCREEN_BACKGROUND_COLOR"

    .line 76
    .line 77
    invoke-virtual {p1, v0, v1}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 78
    .line 79
    .line 80
    move-result v0

    .line 81
    iput v0, p0, LK/i;->i:I

    .line 82
    .line 83
    const-string v0, "android.support.customtabs.trusted.FILE_PROVIDER_AUTHORITY"

    .line 84
    .line 85
    invoke-virtual {p1, v0}, Landroid/os/BaseBundle;->getString(Ljava/lang/String;)Ljava/lang/String;

    .line 86
    .line 87
    .line 88
    move-result-object v0

    .line 89
    iput-object v0, p0, LK/i;->j:Ljava/lang/String;

    .line 90
    .line 91
    const-string v0, "android.support.customtabs.trusted.SPLASH_SCREEN_FADE_OUT_DURATION"

    .line 92
    .line 93
    invoke-virtual {p1, v0, v2}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 94
    .line 95
    .line 96
    move-result v0

    .line 97
    iput v0, p0, LK/i;->k:I

    .line 98
    .line 99
    const-string v0, "android.support.customtabs.trusted.ADDITIONAL_TRUSTED_ORIGINS"

    .line 100
    .line 101
    invoke-virtual {p1, v0}, Landroid/os/BaseBundle;->containsKey(Ljava/lang/String;)Z

    .line 102
    .line 103
    .line 104
    move-result v1

    .line 105
    const/4 v3, 0x0

    .line 106
    if-eqz v1, :cond_0

    .line 107
    .line 108
    invoke-virtual {p1, v0}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;)I

    .line 109
    .line 110
    .line 111
    move-result v0

    .line 112
    invoke-virtual {p2, v0}, Landroid/content/res/Resources;->getStringArray(I)[Ljava/lang/String;

    .line 113
    .line 114
    .line 115
    move-result-object v0

    .line 116
    invoke-static {v0}, Ljava/util/Arrays;->asList([Ljava/lang/Object;)Ljava/util/List;

    .line 117
    .line 118
    .line 119
    move-result-object v0

    .line 120
    iput-object v0, p0, LK/i;->l:Ljava/util/List;

    .line 121
    .line 122
    goto :goto_0

    .line 123
    :cond_0
    iput-object v3, p0, LK/i;->l:Ljava/util/List;

    .line 124
    .line 125
    :goto_0
    const-string v0, "android.support.customtabs.trusted.FALLBACK_STRATEGY"

    .line 126
    .line 127
    invoke-virtual {p1, v0}, Landroid/os/BaseBundle;->getString(Ljava/lang/String;)Ljava/lang/String;

    .line 128
    .line 129
    .line 130
    move-result-object v0

    .line 131
    iput-object v0, p0, LK/i;->m:Ljava/lang/String;

    .line 132
    .line 133
    invoke-static {p1}, LK/i;->a(Landroid/os/Bundle;)Lo/o;

    .line 134
    .line 135
    .line 136
    move-result-object v0

    .line 137
    iput-object v0, p0, LK/i;->n:Lo/o;

    .line 138
    .line 139
    const-string v0, "android.support.customtabs.trusted.SCREEN_ORIENTATION"

    .line 140
    .line 141
    invoke-virtual {p1, v0}, Landroid/os/BaseBundle;->getString(Ljava/lang/String;)Ljava/lang/String;

    .line 142
    .line 143
    .line 144
    move-result-object v0

    .line 145
    invoke-direct {p0, v0}, LK/i;->c(Ljava/lang/String;)I

    .line 146
    .line 147
    .line 148
    move-result v0

    .line 149
    iput v0, p0, LK/i;->o:I

    .line 150
    .line 151
    const-string v0, "android.support.customtabs.trusted.METADATA_SHARE_TARGET"

    .line 152
    .line 153
    invoke-virtual {p1, v0, v2}, Landroid/os/BaseBundle;->getInt(Ljava/lang/String;I)I

    .line 154
    .line 155
    .line 156
    move-result v0

    .line 157
    if-nez v0, :cond_1

    .line 158
    .line 159
    goto :goto_1

    .line 160
    :cond_1
    invoke-virtual {p2, v0}, Landroid/content/res/Resources;->getString(I)Ljava/lang/String;

    .line 161
    .line 162
    .line 163
    move-result-object v3

    .line 164
    :goto_1
    iput-object v3, p0, LK/i;->p:Ljava/lang/String;

    .line 165
    .line 166
    const-string p2, "android.support.customtabs.trusted.FILE_HANDLING_ACTION_URL"

    .line 167
    .line 168
    invoke-virtual {p1, p2}, Landroid/os/BaseBundle;->getString(Ljava/lang/String;)Ljava/lang/String;

    .line 169
    .line 170
    .line 171
    move-result-object p2

    .line 172
    iput-object p2, p0, LK/i;->q:Ljava/lang/String;

    .line 173
    .line 174
    const-string p2, "android.support.customtabs.trusted.LAUNCH_HANDLER_CLIENT_MODE"

    .line 175
    .line 176
    invoke-virtual {p1, p2}, Landroid/os/BaseBundle;->getString(Ljava/lang/String;)Ljava/lang/String;

    .line 177
    .line 178
    .line 179
    move-result-object p2

    .line 180
    invoke-direct {p0, p2}, LK/i;->b(Ljava/lang/String;)I

    .line 181
    .line 182
    .line 183
    move-result p2

    .line 184
    iput p2, p0, LK/i;->r:I

    .line 185
    .line 186
    const-string p2, "android.support.customtabs.trusted.START_CHROME_BEFORE_ANIMATION_COMPLETE"

    .line 187
    .line 188
    const/4 v0, 0x1

    .line 189
    invoke-virtual {p1, p2, v0}, Landroid/os/BaseBundle;->getBoolean(Ljava/lang/String;Z)Z

    .line 190
    .line 191
    .line 192
    move-result p1

    .line 193
    iput-boolean p1, p0, LK/i;->s:Z

    .line 194
    .line 195
    return-void
.end method

.method private static a(Landroid/os/Bundle;)Lo/o;
    .locals 2

    .line 1
    const-string v0, "android.support.customtabs.trusted.DISPLAY_MODE"

    .line 2
    .line 3
    invoke-virtual {p0, v0}, Landroid/os/BaseBundle;->getString(Ljava/lang/String;)Ljava/lang/String;

    .line 4
    .line 5
    .line 6
    move-result-object p0

    .line 7
    const-string v0, "immersive"

    .line 8
    .line 9
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 10
    .line 11
    .line 12
    move-result v0

    .line 13
    const/4 v1, 0x0

    .line 14
    if-eqz v0, :cond_0

    .line 15
    .line 16
    new-instance p0, Lo/o$c;

    .line 17
    .line 18
    invoke-direct {p0, v1, v1}, Lo/o$c;-><init>(ZI)V

    .line 19
    .line 20
    .line 21
    return-object p0

    .line 22
    :cond_0
    const-string v0, "sticky-immersive"

    .line 23
    .line 24
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 25
    .line 26
    .line 27
    move-result v0

    .line 28
    if-eqz v0, :cond_1

    .line 29
    .line 30
    new-instance p0, Lo/o$c;

    .line 31
    .line 32
    const/4 v0, 0x1

    .line 33
    invoke-direct {p0, v0, v1}, Lo/o$c;-><init>(ZI)V

    .line 34
    .line 35
    .line 36
    return-object p0

    .line 37
    :cond_1
    const-string v0, "minimal-ui"

    .line 38
    .line 39
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 40
    .line 41
    .line 42
    move-result v0

    .line 43
    if-eqz v0, :cond_2

    .line 44
    .line 45
    new-instance p0, Lo/o$d;

    .line 46
    .line 47
    invoke-direct {p0}, Lo/o$d;-><init>()V

    .line 48
    .line 49
    .line 50
    return-object p0

    .line 51
    :cond_2
    const-string v0, "browser"

    .line 52
    .line 53
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 54
    .line 55
    .line 56
    move-result p0

    .line 57
    if-eqz p0, :cond_3

    .line 58
    .line 59
    new-instance p0, Lo/o$a;

    .line 60
    .line 61
    invoke-direct {p0}, Lo/o$a;-><init>()V

    .line 62
    .line 63
    .line 64
    return-object p0

    .line 65
    :cond_3
    new-instance p0, Lo/o$b;

    .line 66
    .line 67
    invoke-direct {p0}, Lo/o$b;-><init>()V

    .line 68
    .line 69
    .line 70
    return-object p0
.end method

.method private b(Ljava/lang/String;)I
    .locals 1

    .line 1
    sget-object v0, LK/i;->t:Ljava/util/Map;

    .line 2
    .line 3
    invoke-interface {v0, p1}, Ljava/util/Map;->get(Ljava/lang/Object;)Ljava/lang/Object;

    .line 4
    .line 5
    .line 6
    move-result-object p1

    .line 7
    check-cast p1, Ljava/lang/Integer;

    .line 8
    .line 9
    if-eqz p1, :cond_0

    .line 10
    .line 11
    invoke-virtual {p1}, Ljava/lang/Integer;->intValue()I

    .line 12
    .line 13
    .line 14
    move-result p1

    .line 15
    return p1

    .line 16
    :cond_0
    const/4 p1, 0x0

    .line 17
    return p1
.end method

.method private c(Ljava/lang/String;)I
    .locals 10

    .line 1
    const/4 v0, 0x7

    .line 2
    const/4 v1, 0x6

    .line 3
    const/4 v2, 0x5

    .line 4
    const/4 v3, 0x4

    .line 5
    const/4 v4, 0x3

    .line 6
    const/4 v5, 0x2

    .line 7
    const/4 v6, 0x1

    .line 8
    const/4 v7, 0x0

    .line 9
    if-nez p1, :cond_0

    .line 10
    .line 11
    return v7

    .line 12
    :cond_0
    const/4 v8, -0x1

    .line 13
    invoke-virtual {p1}, Ljava/lang/String;->hashCode()I

    .line 14
    .line 15
    .line 16
    move-result v9

    .line 17
    sparse-switch v9, :sswitch_data_0

    .line 18
    .line 19
    .line 20
    goto/16 :goto_0

    .line 21
    .line 22
    :sswitch_0
    const-string v9, "portrait-secondary"

    .line 23
    .line 24
    invoke-virtual {p1, v9}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 25
    .line 26
    .line 27
    move-result p1

    .line 28
    if-nez p1, :cond_1

    .line 29
    .line 30
    goto/16 :goto_0

    .line 31
    .line 32
    :cond_1
    move v8, v0

    .line 33
    goto :goto_0

    .line 34
    :sswitch_1
    const-string v9, "landscape-primary"

    .line 35
    .line 36
    invoke-virtual {p1, v9}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 37
    .line 38
    .line 39
    move-result p1

    .line 40
    if-nez p1, :cond_2

    .line 41
    .line 42
    goto :goto_0

    .line 43
    :cond_2
    move v8, v1

    .line 44
    goto :goto_0

    .line 45
    :sswitch_2
    const-string v9, "natural"

    .line 46
    .line 47
    invoke-virtual {p1, v9}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 48
    .line 49
    .line 50
    move-result p1

    .line 51
    if-nez p1, :cond_3

    .line 52
    .line 53
    goto :goto_0

    .line 54
    :cond_3
    move v8, v2

    .line 55
    goto :goto_0

    .line 56
    :sswitch_3
    const-string v9, "landscape"

    .line 57
    .line 58
    invoke-virtual {p1, v9}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 59
    .line 60
    .line 61
    move-result p1

    .line 62
    if-nez p1, :cond_4

    .line 63
    .line 64
    goto :goto_0

    .line 65
    :cond_4
    move v8, v3

    .line 66
    goto :goto_0

    .line 67
    :sswitch_4
    const-string v9, "portrait"

    .line 68
    .line 69
    invoke-virtual {p1, v9}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 70
    .line 71
    .line 72
    move-result p1

    .line 73
    if-nez p1, :cond_5

    .line 74
    .line 75
    goto :goto_0

    .line 76
    :cond_5
    move v8, v4

    .line 77
    goto :goto_0

    .line 78
    :sswitch_5
    const-string v9, "any"

    .line 79
    .line 80
    invoke-virtual {p1, v9}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 81
    .line 82
    .line 83
    move-result p1

    .line 84
    if-nez p1, :cond_6

    .line 85
    .line 86
    goto :goto_0

    .line 87
    :cond_6
    move v8, v5

    .line 88
    goto :goto_0

    .line 89
    :sswitch_6
    const-string v9, "landscape-secondary"

    .line 90
    .line 91
    invoke-virtual {p1, v9}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 92
    .line 93
    .line 94
    move-result p1

    .line 95
    if-nez p1, :cond_7

    .line 96
    .line 97
    goto :goto_0

    .line 98
    :cond_7
    move v8, v6

    .line 99
    goto :goto_0

    .line 100
    :sswitch_7
    const-string v9, "portrait-primary"

    .line 101
    .line 102
    invoke-virtual {p1, v9}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 103
    .line 104
    .line 105
    move-result p1

    .line 106
    if-nez p1, :cond_8

    .line 107
    .line 108
    goto :goto_0

    .line 109
    :cond_8
    move v8, v7

    .line 110
    :goto_0
    packed-switch v8, :pswitch_data_0

    .line 111
    .line 112
    .line 113
    return v7

    .line 114
    :pswitch_0
    return v5

    .line 115
    :pswitch_1
    return v4

    .line 116
    :pswitch_2
    const/16 p1, 0x8

    .line 117
    .line 118
    return p1

    .line 119
    :pswitch_3
    return v1

    .line 120
    :pswitch_4
    return v0

    .line 121
    :pswitch_5
    return v2

    .line 122
    :pswitch_6
    return v3

    .line 123
    :pswitch_7
    return v6

    .line 124
    nop

    .line 125
    :sswitch_data_0
    .sparse-switch
        -0x49321e30 -> :sswitch_7
        -0x8c4a71e -> :sswitch_6
        0x179ec -> :sswitch_5
        0x2b77bb9b -> :sswitch_4
        0x5545f2bb -> :sswitch_3
        0x670d1829 -> :sswitch_2
        0x6f02f8f0 -> :sswitch_1
        0x77ef89c2 -> :sswitch_0
    .end sparse-switch

    .line 126
    .line 127
    .line 128
    .line 129
    .line 130
    .line 131
    .line 132
    .line 133
    .line 134
    .line 135
    .line 136
    .line 137
    .line 138
    .line 139
    .line 140
    .line 141
    :pswitch_data_0
    .packed-switch 0x0
        :pswitch_7
        :pswitch_6
        :pswitch_5
        :pswitch_4
        :pswitch_3
        :pswitch_2
        :pswitch_1
        :pswitch_0
    .end packed-switch
.end method

.method public static d(Landroid/content/Context;)LK/i;
    .locals 5

    .line 1
    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    new-instance v1, Landroid/os/Bundle;

    .line 6
    .line 7
    invoke-direct {v1}, Landroid/os/Bundle;-><init>()V

    .line 8
    .line 9
    .line 10
    :try_start_0
    invoke-virtual {p0}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 11
    .line 12
    .line 13
    move-result-object v2

    .line 14
    new-instance v3, Landroid/content/ComponentName;

    .line 15
    .line 16
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    .line 17
    .line 18
    .line 19
    move-result-object v4

    .line 20
    invoke-direct {v3, p0, v4}, Landroid/content/ComponentName;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    .line 21
    .line 22
    .line 23
    const/16 v4, 0x80

    .line 24
    .line 25
    invoke-virtual {v2, v3, v4}, Landroid/content/pm/PackageManager;->getActivityInfo(Landroid/content/ComponentName;I)Landroid/content/pm/ActivityInfo;

    .line 26
    .line 27
    .line 28
    move-result-object v2

    .line 29
    iget-object v2, v2, Landroid/content/pm/ActivityInfo;->metaData:Landroid/os/Bundle;

    .line 30
    .line 31
    if-eqz v2, :cond_0

    .line 32
    .line 33
    invoke-virtual {v1, v2}, Landroid/os/Bundle;->putAll(Landroid/os/Bundle;)V

    .line 34
    .line 35
    .line 36
    :cond_0
    instance-of v2, p0, Landroid/app/Activity;

    .line 37
    .line 38
    if-eqz v2, :cond_1

    .line 39
    .line 40
    check-cast p0, Landroid/app/Activity;

    .line 41
    .line 42
    invoke-virtual {p0}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 43
    .line 44
    .line 45
    move-result-object v2

    .line 46
    invoke-virtual {p0}, Landroid/app/Activity;->getComponentName()Landroid/content/ComponentName;

    .line 47
    .line 48
    .line 49
    move-result-object p0

    .line 50
    invoke-virtual {v2, p0, v4}, Landroid/content/pm/PackageManager;->getActivityInfo(Landroid/content/ComponentName;I)Landroid/content/pm/ActivityInfo;

    .line 51
    .line 52
    .line 53
    move-result-object p0

    .line 54
    iget-object v2, p0, Landroid/content/pm/ActivityInfo;->targetActivity:Ljava/lang/String;

    .line 55
    .line 56
    if-eqz v2, :cond_1

    .line 57
    .line 58
    iget-object p0, p0, Landroid/content/pm/ActivityInfo;->metaData:Landroid/os/Bundle;

    .line 59
    .line 60
    if-eqz p0, :cond_1

    .line 61
    .line 62
    invoke-virtual {v1, p0}, Landroid/os/Bundle;->putAll(Landroid/os/Bundle;)V
    :try_end_0
    .catch Landroid/content/pm/PackageManager$NameNotFoundException; {:try_start_0 .. :try_end_0} :catch_0

    .line 63
    .line 64
    .line 65
    :catch_0
    :cond_1
    new-instance p0, LK/i;

    .line 66
    .line 67
    invoke-direct {p0, v1, v0}, LK/i;-><init>(Landroid/os/Bundle;Landroid/content/res/Resources;)V

    .line 68
    .line 69
    .line 70
    return-object p0
.end method
