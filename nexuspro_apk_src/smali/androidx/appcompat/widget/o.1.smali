.class Landroidx/appcompat/widget/o;
.super Ljava/lang/Object;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Landroidx/appcompat/widget/o$d;,
        Landroidx/appcompat/widget/o$c;,
        Landroidx/appcompat/widget/o$e;
    }
.end annotation


# instance fields
.field private final a:Landroid/widget/TextView;

.field private b:Landroidx/appcompat/widget/I;

.field private c:Landroidx/appcompat/widget/I;

.field private d:Landroidx/appcompat/widget/I;

.field private e:Landroidx/appcompat/widget/I;

.field private f:Landroidx/appcompat/widget/I;

.field private g:Landroidx/appcompat/widget/I;

.field private h:Landroidx/appcompat/widget/I;

.field private final i:Landroidx/appcompat/widget/q;

.field private j:I

.field private k:I

.field private l:Landroid/graphics/Typeface;

.field private m:Z


# direct methods
.method constructor <init>(Landroid/widget/TextView;)V
    .locals 1

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 2
    .line 3
    .line 4
    const/4 v0, 0x0

    .line 5
    iput v0, p0, Landroidx/appcompat/widget/o;->j:I

    .line 6
    .line 7
    const/4 v0, -0x1

    .line 8
    iput v0, p0, Landroidx/appcompat/widget/o;->k:I

    .line 9
    .line 10
    iput-object p1, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 11
    .line 12
    new-instance v0, Landroidx/appcompat/widget/q;

    .line 13
    .line 14
    invoke-direct {v0, p1}, Landroidx/appcompat/widget/q;-><init>(Landroid/widget/TextView;)V

    .line 15
    .line 16
    .line 17
    iput-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 18
    .line 19
    return-void
.end method

.method private B(IF)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0, p1, p2}, Landroidx/appcompat/widget/q;->t(IF)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method private C(Landroid/content/Context;Landroidx/appcompat/widget/K;)V
    .locals 10

    .line 1
    sget v0, Ld/i;->C1:I

    .line 2
    .line 3
    iget v1, p0, Landroidx/appcompat/widget/o;->j:I

    .line 4
    .line 5
    invoke-virtual {p2, v0, v1}, Landroidx/appcompat/widget/K;->i(II)I

    .line 6
    .line 7
    .line 8
    move-result v0

    .line 9
    iput v0, p0, Landroidx/appcompat/widget/o;->j:I

    .line 10
    .line 11
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 12
    .line 13
    const/4 v1, 0x2

    .line 14
    const/4 v2, -0x1

    .line 15
    const/16 v3, 0x1c

    .line 16
    .line 17
    if-lt v0, v3, :cond_0

    .line 18
    .line 19
    sget v4, Ld/i;->E1:I

    .line 20
    .line 21
    invoke-virtual {p2, v4, v2}, Landroidx/appcompat/widget/K;->i(II)I

    .line 22
    .line 23
    .line 24
    move-result v4

    .line 25
    iput v4, p0, Landroidx/appcompat/widget/o;->k:I

    .line 26
    .line 27
    if-eq v4, v2, :cond_0

    .line 28
    .line 29
    iget v4, p0, Landroidx/appcompat/widget/o;->j:I

    .line 30
    .line 31
    and-int/2addr v4, v1

    .line 32
    iput v4, p0, Landroidx/appcompat/widget/o;->j:I

    .line 33
    .line 34
    :cond_0
    sget v4, Ld/i;->D1:I

    .line 35
    .line 36
    invoke-virtual {p2, v4}, Landroidx/appcompat/widget/K;->p(I)Z

    .line 37
    .line 38
    .line 39
    move-result v4

    .line 40
    const/4 v5, 0x1

    .line 41
    const/4 v6, 0x0

    .line 42
    if-nez v4, :cond_5

    .line 43
    .line 44
    sget v4, Ld/i;->F1:I

    .line 45
    .line 46
    invoke-virtual {p2, v4}, Landroidx/appcompat/widget/K;->p(I)Z

    .line 47
    .line 48
    .line 49
    move-result v4

    .line 50
    if-eqz v4, :cond_1

    .line 51
    .line 52
    goto :goto_0

    .line 53
    :cond_1
    sget p1, Ld/i;->B1:I

    .line 54
    .line 55
    invoke-virtual {p2, p1}, Landroidx/appcompat/widget/K;->p(I)Z

    .line 56
    .line 57
    .line 58
    move-result p1

    .line 59
    if-eqz p1, :cond_e

    .line 60
    .line 61
    iput-boolean v6, p0, Landroidx/appcompat/widget/o;->m:Z

    .line 62
    .line 63
    sget p1, Ld/i;->B1:I

    .line 64
    .line 65
    invoke-virtual {p2, p1, v5}, Landroidx/appcompat/widget/K;->i(II)I

    .line 66
    .line 67
    .line 68
    move-result p1

    .line 69
    if-eq p1, v5, :cond_4

    .line 70
    .line 71
    if-eq p1, v1, :cond_3

    .line 72
    .line 73
    const/4 p2, 0x3

    .line 74
    if-eq p1, p2, :cond_2

    .line 75
    .line 76
    goto/16 :goto_6

    .line 77
    .line 78
    :cond_2
    sget-object p1, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    .line 79
    .line 80
    iput-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 81
    .line 82
    return-void

    .line 83
    :cond_3
    sget-object p1, Landroid/graphics/Typeface;->SERIF:Landroid/graphics/Typeface;

    .line 84
    .line 85
    iput-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 86
    .line 87
    return-void

    .line 88
    :cond_4
    sget-object p1, Landroid/graphics/Typeface;->SANS_SERIF:Landroid/graphics/Typeface;

    .line 89
    .line 90
    iput-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 91
    .line 92
    return-void

    .line 93
    :cond_5
    :goto_0
    const/4 v4, 0x0

    .line 94
    iput-object v4, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 95
    .line 96
    sget v4, Ld/i;->F1:I

    .line 97
    .line 98
    invoke-virtual {p2, v4}, Landroidx/appcompat/widget/K;->p(I)Z

    .line 99
    .line 100
    .line 101
    move-result v4

    .line 102
    if-eqz v4, :cond_6

    .line 103
    .line 104
    sget v4, Ld/i;->F1:I

    .line 105
    .line 106
    goto :goto_1

    .line 107
    :cond_6
    sget v4, Ld/i;->D1:I

    .line 108
    .line 109
    :goto_1
    iget v7, p0, Landroidx/appcompat/widget/o;->k:I

    .line 110
    .line 111
    iget v8, p0, Landroidx/appcompat/widget/o;->j:I

    .line 112
    .line 113
    invoke-virtual {p1}, Landroid/content/Context;->isRestricted()Z

    .line 114
    .line 115
    .line 116
    move-result p1

    .line 117
    if-nez p1, :cond_b

    .line 118
    .line 119
    new-instance p1, Ljava/lang/ref/WeakReference;

    .line 120
    .line 121
    iget-object v9, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 122
    .line 123
    invoke-direct {p1, v9}, Ljava/lang/ref/WeakReference;-><init>(Ljava/lang/Object;)V

    .line 124
    .line 125
    .line 126
    new-instance v9, Landroidx/appcompat/widget/o$a;

    .line 127
    .line 128
    invoke-direct {v9, p0, v7, v8, p1}, Landroidx/appcompat/widget/o$a;-><init>(Landroidx/appcompat/widget/o;IILjava/lang/ref/WeakReference;)V

    .line 129
    .line 130
    .line 131
    :try_start_0
    iget p1, p0, Landroidx/appcompat/widget/o;->j:I

    .line 132
    .line 133
    invoke-virtual {p2, v4, p1, v9}, Landroidx/appcompat/widget/K;->h(IILandroidx/core/content/res/f$e;)Landroid/graphics/Typeface;

    .line 134
    .line 135
    .line 136
    move-result-object p1

    .line 137
    if-eqz p1, :cond_9

    .line 138
    .line 139
    if-lt v0, v3, :cond_8

    .line 140
    .line 141
    iget v0, p0, Landroidx/appcompat/widget/o;->k:I

    .line 142
    .line 143
    if-eq v0, v2, :cond_8

    .line 144
    .line 145
    invoke-static {p1, v6}, Landroid/graphics/Typeface;->create(Landroid/graphics/Typeface;I)Landroid/graphics/Typeface;

    .line 146
    .line 147
    .line 148
    move-result-object p1

    .line 149
    iget v0, p0, Landroidx/appcompat/widget/o;->k:I

    .line 150
    .line 151
    iget v7, p0, Landroidx/appcompat/widget/o;->j:I

    .line 152
    .line 153
    and-int/2addr v7, v1

    .line 154
    if-eqz v7, :cond_7

    .line 155
    .line 156
    move v7, v5

    .line 157
    goto :goto_2

    .line 158
    :cond_7
    move v7, v6

    .line 159
    :goto_2
    invoke-static {p1, v0, v7}, Landroidx/appcompat/widget/o$e;->a(Landroid/graphics/Typeface;IZ)Landroid/graphics/Typeface;

    .line 160
    .line 161
    .line 162
    move-result-object p1

    .line 163
    iput-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 164
    .line 165
    goto :goto_3

    .line 166
    :cond_8
    iput-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 167
    .line 168
    :cond_9
    :goto_3
    iget-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 169
    .line 170
    if-nez p1, :cond_a

    .line 171
    .line 172
    move p1, v5

    .line 173
    goto :goto_4

    .line 174
    :cond_a
    move p1, v6

    .line 175
    :goto_4
    iput-boolean p1, p0, Landroidx/appcompat/widget/o;->m:Z
    :try_end_0
    .catch Ljava/lang/UnsupportedOperationException; {:try_start_0 .. :try_end_0} :catch_0
    .catch Landroid/content/res/Resources$NotFoundException; {:try_start_0 .. :try_end_0} :catch_0

    .line 176
    .line 177
    :catch_0
    :cond_b
    iget-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 178
    .line 179
    if-nez p1, :cond_e

    .line 180
    .line 181
    invoke-virtual {p2, v4}, Landroidx/appcompat/widget/K;->m(I)Ljava/lang/String;

    .line 182
    .line 183
    .line 184
    move-result-object p1

    .line 185
    if-eqz p1, :cond_e

    .line 186
    .line 187
    sget p2, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 188
    .line 189
    if-lt p2, v3, :cond_d

    .line 190
    .line 191
    iget p2, p0, Landroidx/appcompat/widget/o;->k:I

    .line 192
    .line 193
    if-eq p2, v2, :cond_d

    .line 194
    .line 195
    invoke-static {p1, v6}, Landroid/graphics/Typeface;->create(Ljava/lang/String;I)Landroid/graphics/Typeface;

    .line 196
    .line 197
    .line 198
    move-result-object p1

    .line 199
    iget p2, p0, Landroidx/appcompat/widget/o;->k:I

    .line 200
    .line 201
    iget v0, p0, Landroidx/appcompat/widget/o;->j:I

    .line 202
    .line 203
    and-int/2addr v0, v1

    .line 204
    if-eqz v0, :cond_c

    .line 205
    .line 206
    goto :goto_5

    .line 207
    :cond_c
    move v5, v6

    .line 208
    :goto_5
    invoke-static {p1, p2, v5}, Landroidx/appcompat/widget/o$e;->a(Landroid/graphics/Typeface;IZ)Landroid/graphics/Typeface;

    .line 209
    .line 210
    .line 211
    move-result-object p1

    .line 212
    iput-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 213
    .line 214
    goto :goto_6

    .line 215
    :cond_d
    iget p2, p0, Landroidx/appcompat/widget/o;->j:I

    .line 216
    .line 217
    invoke-static {p1, p2}, Landroid/graphics/Typeface;->create(Ljava/lang/String;I)Landroid/graphics/Typeface;

    .line 218
    .line 219
    .line 220
    move-result-object p1

    .line 221
    iput-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 222
    .line 223
    :cond_e
    :goto_6
    return-void
.end method

.method private a(Landroid/graphics/drawable/Drawable;Landroidx/appcompat/widget/I;)V
    .locals 1

    .line 1
    if-eqz p1, :cond_0

    .line 2
    .line 3
    if-eqz p2, :cond_0

    .line 4
    .line 5
    iget-object v0, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 6
    .line 7
    invoke-virtual {v0}, Landroid/view/View;->getDrawableState()[I

    .line 8
    .line 9
    .line 10
    move-result-object v0

    .line 11
    invoke-static {p1, p2, v0}, Landroidx/appcompat/widget/f;->g(Landroid/graphics/drawable/Drawable;Landroidx/appcompat/widget/I;[I)V

    .line 12
    .line 13
    .line 14
    :cond_0
    return-void
.end method

.method private static d(Landroid/content/Context;Landroidx/appcompat/widget/f;I)Landroidx/appcompat/widget/I;
    .locals 0

    .line 1
    invoke-virtual {p1, p0, p2}, Landroidx/appcompat/widget/f;->e(Landroid/content/Context;I)Landroid/content/res/ColorStateList;

    .line 2
    .line 3
    .line 4
    move-result-object p0

    .line 5
    if-eqz p0, :cond_0

    .line 6
    .line 7
    new-instance p1, Landroidx/appcompat/widget/I;

    .line 8
    .line 9
    invoke-direct {p1}, Landroidx/appcompat/widget/I;-><init>()V

    .line 10
    .line 11
    .line 12
    const/4 p2, 0x1

    .line 13
    iput-boolean p2, p1, Landroidx/appcompat/widget/I;->d:Z

    .line 14
    .line 15
    iput-object p0, p1, Landroidx/appcompat/widget/I;->a:Landroid/content/res/ColorStateList;

    .line 16
    .line 17
    return-object p1

    .line 18
    :cond_0
    const/4 p0, 0x0

    .line 19
    return-object p0
.end method

.method private y(Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;)V
    .locals 5

    .line 1
    const/4 v0, 0x3

    .line 2
    const/4 v1, 0x1

    .line 3
    const/4 v2, 0x0

    .line 4
    const/4 v3, 0x2

    .line 5
    if-nez p5, :cond_b

    .line 6
    .line 7
    if-eqz p6, :cond_0

    .line 8
    .line 9
    goto :goto_8

    .line 10
    :cond_0
    if-nez p1, :cond_2

    .line 11
    .line 12
    if-nez p2, :cond_2

    .line 13
    .line 14
    if-nez p3, :cond_2

    .line 15
    .line 16
    if-eqz p4, :cond_1

    .line 17
    .line 18
    goto :goto_0

    .line 19
    :cond_1
    return-void

    .line 20
    :cond_2
    :goto_0
    iget-object p5, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 21
    .line 22
    invoke-virtual {p5}, Landroid/widget/TextView;->getCompoundDrawablesRelative()[Landroid/graphics/drawable/Drawable;

    .line 23
    .line 24
    .line 25
    move-result-object p5

    .line 26
    aget-object p6, p5, v2

    .line 27
    .line 28
    if-nez p6, :cond_8

    .line 29
    .line 30
    aget-object v4, p5, v3

    .line 31
    .line 32
    if-eqz v4, :cond_3

    .line 33
    .line 34
    goto :goto_5

    .line 35
    :cond_3
    iget-object p5, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 36
    .line 37
    invoke-virtual {p5}, Landroid/widget/TextView;->getCompoundDrawables()[Landroid/graphics/drawable/Drawable;

    .line 38
    .line 39
    .line 40
    move-result-object p5

    .line 41
    iget-object p6, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 42
    .line 43
    if-eqz p1, :cond_4

    .line 44
    .line 45
    goto :goto_1

    .line 46
    :cond_4
    aget-object p1, p5, v2

    .line 47
    .line 48
    :goto_1
    if-eqz p2, :cond_5

    .line 49
    .line 50
    goto :goto_2

    .line 51
    :cond_5
    aget-object p2, p5, v1

    .line 52
    .line 53
    :goto_2
    if-eqz p3, :cond_6

    .line 54
    .line 55
    goto :goto_3

    .line 56
    :cond_6
    aget-object p3, p5, v3

    .line 57
    .line 58
    :goto_3
    if-eqz p4, :cond_7

    .line 59
    .line 60
    goto :goto_4

    .line 61
    :cond_7
    aget-object p4, p5, v0

    .line 62
    .line 63
    :goto_4
    invoke-virtual {p6, p1, p2, p3, p4}, Landroid/widget/TextView;->setCompoundDrawablesWithIntrinsicBounds(Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;)V

    .line 64
    .line 65
    .line 66
    return-void

    .line 67
    :cond_8
    :goto_5
    if-eqz p2, :cond_9

    .line 68
    .line 69
    goto :goto_6

    .line 70
    :cond_9
    aget-object p2, p5, v1

    .line 71
    .line 72
    :goto_6
    if-eqz p4, :cond_a

    .line 73
    .line 74
    goto :goto_7

    .line 75
    :cond_a
    aget-object p4, p5, v0

    .line 76
    .line 77
    :goto_7
    iget-object p1, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 78
    .line 79
    aget-object p3, p5, v3

    .line 80
    .line 81
    invoke-virtual {p1, p6, p2, p3, p4}, Landroid/widget/TextView;->setCompoundDrawablesRelativeWithIntrinsicBounds(Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;)V

    .line 82
    .line 83
    .line 84
    return-void

    .line 85
    :cond_b
    :goto_8
    iget-object p1, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 86
    .line 87
    invoke-virtual {p1}, Landroid/widget/TextView;->getCompoundDrawablesRelative()[Landroid/graphics/drawable/Drawable;

    .line 88
    .line 89
    .line 90
    move-result-object p1

    .line 91
    if-eqz p5, :cond_c

    .line 92
    .line 93
    goto :goto_9

    .line 94
    :cond_c
    aget-object p5, p1, v2

    .line 95
    .line 96
    :goto_9
    if-eqz p2, :cond_d

    .line 97
    .line 98
    goto :goto_a

    .line 99
    :cond_d
    aget-object p2, p1, v1

    .line 100
    .line 101
    :goto_a
    if-eqz p6, :cond_e

    .line 102
    .line 103
    goto :goto_b

    .line 104
    :cond_e
    aget-object p6, p1, v3

    .line 105
    .line 106
    :goto_b
    iget-object p3, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 107
    .line 108
    if-eqz p4, :cond_f

    .line 109
    .line 110
    goto :goto_c

    .line 111
    :cond_f
    aget-object p4, p1, v0

    .line 112
    .line 113
    :goto_c
    invoke-virtual {p3, p5, p2, p6, p4}, Landroid/widget/TextView;->setCompoundDrawablesRelativeWithIntrinsicBounds(Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;)V

    .line 114
    .line 115
    .line 116
    return-void
.end method

.method private z()V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->h:Landroidx/appcompat/widget/I;

    .line 2
    .line 3
    iput-object v0, p0, Landroidx/appcompat/widget/o;->b:Landroidx/appcompat/widget/I;

    .line 4
    .line 5
    iput-object v0, p0, Landroidx/appcompat/widget/o;->c:Landroidx/appcompat/widget/I;

    .line 6
    .line 7
    iput-object v0, p0, Landroidx/appcompat/widget/o;->d:Landroidx/appcompat/widget/I;

    .line 8
    .line 9
    iput-object v0, p0, Landroidx/appcompat/widget/o;->e:Landroidx/appcompat/widget/I;

    .line 10
    .line 11
    iput-object v0, p0, Landroidx/appcompat/widget/o;->f:Landroidx/appcompat/widget/I;

    .line 12
    .line 13
    iput-object v0, p0, Landroidx/appcompat/widget/o;->g:Landroidx/appcompat/widget/I;

    .line 14
    .line 15
    return-void
.end method


# virtual methods
.method A(IF)V
    .locals 1

    .line 1
    sget-boolean v0, Landroidx/appcompat/widget/W;->a:Z

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    invoke-virtual {p0}, Landroidx/appcompat/widget/o;->l()Z

    .line 6
    .line 7
    .line 8
    move-result v0

    .line 9
    if-nez v0, :cond_0

    .line 10
    .line 11
    invoke-direct {p0, p1, p2}, Landroidx/appcompat/widget/o;->B(IF)V

    .line 12
    .line 13
    .line 14
    :cond_0
    return-void
.end method

.method b()V
    .locals 5

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->b:Landroidx/appcompat/widget/I;

    .line 2
    .line 3
    const/4 v1, 0x2

    .line 4
    const/4 v2, 0x0

    .line 5
    if-nez v0, :cond_0

    .line 6
    .line 7
    iget-object v0, p0, Landroidx/appcompat/widget/o;->c:Landroidx/appcompat/widget/I;

    .line 8
    .line 9
    if-nez v0, :cond_0

    .line 10
    .line 11
    iget-object v0, p0, Landroidx/appcompat/widget/o;->d:Landroidx/appcompat/widget/I;

    .line 12
    .line 13
    if-nez v0, :cond_0

    .line 14
    .line 15
    iget-object v0, p0, Landroidx/appcompat/widget/o;->e:Landroidx/appcompat/widget/I;

    .line 16
    .line 17
    if-eqz v0, :cond_1

    .line 18
    .line 19
    :cond_0
    iget-object v0, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 20
    .line 21
    invoke-virtual {v0}, Landroid/widget/TextView;->getCompoundDrawables()[Landroid/graphics/drawable/Drawable;

    .line 22
    .line 23
    .line 24
    move-result-object v0

    .line 25
    aget-object v3, v0, v2

    .line 26
    .line 27
    iget-object v4, p0, Landroidx/appcompat/widget/o;->b:Landroidx/appcompat/widget/I;

    .line 28
    .line 29
    invoke-direct {p0, v3, v4}, Landroidx/appcompat/widget/o;->a(Landroid/graphics/drawable/Drawable;Landroidx/appcompat/widget/I;)V

    .line 30
    .line 31
    .line 32
    const/4 v3, 0x1

    .line 33
    aget-object v3, v0, v3

    .line 34
    .line 35
    iget-object v4, p0, Landroidx/appcompat/widget/o;->c:Landroidx/appcompat/widget/I;

    .line 36
    .line 37
    invoke-direct {p0, v3, v4}, Landroidx/appcompat/widget/o;->a(Landroid/graphics/drawable/Drawable;Landroidx/appcompat/widget/I;)V

    .line 38
    .line 39
    .line 40
    aget-object v3, v0, v1

    .line 41
    .line 42
    iget-object v4, p0, Landroidx/appcompat/widget/o;->d:Landroidx/appcompat/widget/I;

    .line 43
    .line 44
    invoke-direct {p0, v3, v4}, Landroidx/appcompat/widget/o;->a(Landroid/graphics/drawable/Drawable;Landroidx/appcompat/widget/I;)V

    .line 45
    .line 46
    .line 47
    const/4 v3, 0x3

    .line 48
    aget-object v0, v0, v3

    .line 49
    .line 50
    iget-object v3, p0, Landroidx/appcompat/widget/o;->e:Landroidx/appcompat/widget/I;

    .line 51
    .line 52
    invoke-direct {p0, v0, v3}, Landroidx/appcompat/widget/o;->a(Landroid/graphics/drawable/Drawable;Landroidx/appcompat/widget/I;)V

    .line 53
    .line 54
    .line 55
    :cond_1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->f:Landroidx/appcompat/widget/I;

    .line 56
    .line 57
    if-nez v0, :cond_3

    .line 58
    .line 59
    iget-object v0, p0, Landroidx/appcompat/widget/o;->g:Landroidx/appcompat/widget/I;

    .line 60
    .line 61
    if-eqz v0, :cond_2

    .line 62
    .line 63
    goto :goto_0

    .line 64
    :cond_2
    return-void

    .line 65
    :cond_3
    :goto_0
    iget-object v0, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 66
    .line 67
    invoke-virtual {v0}, Landroid/widget/TextView;->getCompoundDrawablesRelative()[Landroid/graphics/drawable/Drawable;

    .line 68
    .line 69
    .line 70
    move-result-object v0

    .line 71
    aget-object v2, v0, v2

    .line 72
    .line 73
    iget-object v3, p0, Landroidx/appcompat/widget/o;->f:Landroidx/appcompat/widget/I;

    .line 74
    .line 75
    invoke-direct {p0, v2, v3}, Landroidx/appcompat/widget/o;->a(Landroid/graphics/drawable/Drawable;Landroidx/appcompat/widget/I;)V

    .line 76
    .line 77
    .line 78
    aget-object v0, v0, v1

    .line 79
    .line 80
    iget-object v1, p0, Landroidx/appcompat/widget/o;->g:Landroidx/appcompat/widget/I;

    .line 81
    .line 82
    invoke-direct {p0, v0, v1}, Landroidx/appcompat/widget/o;->a(Landroid/graphics/drawable/Drawable;Landroidx/appcompat/widget/I;)V

    .line 83
    .line 84
    .line 85
    return-void
.end method

.method c()V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroidx/appcompat/widget/q;->a()V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method e()I
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroidx/appcompat/widget/q;->f()I

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    return v0
.end method

.method f()I
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroidx/appcompat/widget/q;->g()I

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    return v0
.end method

.method g()I
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroidx/appcompat/widget/q;->h()I

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    return v0
.end method

.method h()[I
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroidx/appcompat/widget/q;->i()[I

    .line 4
    .line 5
    .line 6
    move-result-object v0

    .line 7
    return-object v0
.end method

.method i()I
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroidx/appcompat/widget/q;->j()I

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    return v0
.end method

.method j()Landroid/content/res/ColorStateList;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->h:Landroidx/appcompat/widget/I;

    .line 2
    .line 3
    if-eqz v0, :cond_0

    .line 4
    .line 5
    iget-object v0, v0, Landroidx/appcompat/widget/I;->a:Landroid/content/res/ColorStateList;

    .line 6
    .line 7
    return-object v0

    .line 8
    :cond_0
    const/4 v0, 0x0

    .line 9
    return-object v0
.end method

.method k()Landroid/graphics/PorterDuff$Mode;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->h:Landroidx/appcompat/widget/I;

    .line 2
    .line 3
    if-eqz v0, :cond_0

    .line 4
    .line 5
    iget-object v0, v0, Landroidx/appcompat/widget/I;->b:Landroid/graphics/PorterDuff$Mode;

    .line 6
    .line 7
    return-object v0

    .line 8
    :cond_0
    const/4 v0, 0x0

    .line 9
    return-object v0
.end method

.method l()Z
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroidx/appcompat/widget/q;->n()Z

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    return v0
.end method

.method m(Landroid/util/AttributeSet;I)V
    .locals 16

    move-object/from16 v0, p0

    move-object/from16 v4, p1

    move/from16 v6, p2

    .line 1
    iget-object v1, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-virtual {v1}, Landroid/view/View;->getContext()Landroid/content/Context;

    move-result-object v8

    .line 2
    invoke-static {}, Landroidx/appcompat/widget/f;->b()Landroidx/appcompat/widget/f;

    move-result-object v9

    .line 3
    sget-object v1, Ld/i;->K:[I

    const/4 v10, 0x0

    invoke-static {v8, v4, v1, v6, v10}, Landroidx/appcompat/widget/K;->s(Landroid/content/Context;Landroid/util/AttributeSet;[III)Landroidx/appcompat/widget/K;

    move-result-object v11

    .line 4
    iget-object v1, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-virtual {v1}, Landroid/view/View;->getContext()Landroid/content/Context;

    move-result-object v2

    sget-object v3, Ld/i;->K:[I

    .line 5
    invoke-virtual {v11}, Landroidx/appcompat/widget/K;->o()Landroid/content/res/TypedArray;

    move-result-object v5

    const/4 v7, 0x0

    .line 6
    invoke-static/range {v1 .. v7}, Landroidx/core/view/v;->v(Landroid/view/View;Landroid/content/Context;[ILandroid/util/AttributeSet;Landroid/content/res/TypedArray;II)V

    .line 7
    sget v1, Ld/i;->L:I

    const/4 v7, -0x1

    invoke-virtual {v11, v1, v7}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v1

    .line 8
    sget v2, Ld/i;->O:I

    invoke-virtual {v11, v2}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v2

    if-eqz v2, :cond_0

    .line 9
    sget v2, Ld/i;->O:I

    .line 10
    invoke-virtual {v11, v2, v10}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v2

    .line 11
    invoke-static {v8, v9, v2}, Landroidx/appcompat/widget/o;->d(Landroid/content/Context;Landroidx/appcompat/widget/f;I)Landroidx/appcompat/widget/I;

    move-result-object v2

    iput-object v2, v0, Landroidx/appcompat/widget/o;->b:Landroidx/appcompat/widget/I;

    .line 12
    :cond_0
    sget v2, Ld/i;->M:I

    invoke-virtual {v11, v2}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v2

    if-eqz v2, :cond_1

    .line 13
    sget v2, Ld/i;->M:I

    .line 14
    invoke-virtual {v11, v2, v10}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v2

    .line 15
    invoke-static {v8, v9, v2}, Landroidx/appcompat/widget/o;->d(Landroid/content/Context;Landroidx/appcompat/widget/f;I)Landroidx/appcompat/widget/I;

    move-result-object v2

    iput-object v2, v0, Landroidx/appcompat/widget/o;->c:Landroidx/appcompat/widget/I;

    .line 16
    :cond_1
    sget v2, Ld/i;->P:I

    invoke-virtual {v11, v2}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v2

    if-eqz v2, :cond_2

    .line 17
    sget v2, Ld/i;->P:I

    .line 18
    invoke-virtual {v11, v2, v10}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v2

    .line 19
    invoke-static {v8, v9, v2}, Landroidx/appcompat/widget/o;->d(Landroid/content/Context;Landroidx/appcompat/widget/f;I)Landroidx/appcompat/widget/I;

    move-result-object v2

    iput-object v2, v0, Landroidx/appcompat/widget/o;->d:Landroidx/appcompat/widget/I;

    .line 20
    :cond_2
    sget v2, Ld/i;->N:I

    invoke-virtual {v11, v2}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v2

    if-eqz v2, :cond_3

    .line 21
    sget v2, Ld/i;->N:I

    .line 22
    invoke-virtual {v11, v2, v10}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v2

    .line 23
    invoke-static {v8, v9, v2}, Landroidx/appcompat/widget/o;->d(Landroid/content/Context;Landroidx/appcompat/widget/f;I)Landroidx/appcompat/widget/I;

    move-result-object v2

    iput-object v2, v0, Landroidx/appcompat/widget/o;->e:Landroidx/appcompat/widget/I;

    .line 24
    :cond_3
    sget v2, Ld/i;->Q:I

    invoke-virtual {v11, v2}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v2

    if-eqz v2, :cond_4

    .line 25
    sget v2, Ld/i;->Q:I

    .line 26
    invoke-virtual {v11, v2, v10}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v2

    .line 27
    invoke-static {v8, v9, v2}, Landroidx/appcompat/widget/o;->d(Landroid/content/Context;Landroidx/appcompat/widget/f;I)Landroidx/appcompat/widget/I;

    move-result-object v2

    iput-object v2, v0, Landroidx/appcompat/widget/o;->f:Landroidx/appcompat/widget/I;

    .line 28
    :cond_4
    sget v2, Ld/i;->R:I

    invoke-virtual {v11, v2}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v2

    if-eqz v2, :cond_5

    .line 29
    sget v2, Ld/i;->R:I

    .line 30
    invoke-virtual {v11, v2, v10}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v2

    .line 31
    invoke-static {v8, v9, v2}, Landroidx/appcompat/widget/o;->d(Landroid/content/Context;Landroidx/appcompat/widget/f;I)Landroidx/appcompat/widget/I;

    move-result-object v2

    iput-object v2, v0, Landroidx/appcompat/widget/o;->g:Landroidx/appcompat/widget/I;

    .line 32
    :cond_5
    invoke-virtual {v11}, Landroidx/appcompat/widget/K;->u()V

    .line 33
    iget-object v2, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 34
    invoke-virtual {v2}, Landroid/widget/TextView;->getTransformationMethod()Landroid/text/method/TransformationMethod;

    move-result-object v2

    instance-of v2, v2, Landroid/text/method/PasswordTransformationMethod;

    const/16 v3, 0x1a

    if-eq v1, v7, :cond_9

    .line 35
    sget-object v12, Ld/i;->z1:[I

    invoke-static {v8, v1, v12}, Landroidx/appcompat/widget/K;->q(Landroid/content/Context;I[I)Landroidx/appcompat/widget/K;

    move-result-object v1

    if-nez v2, :cond_6

    .line 36
    sget v12, Ld/i;->H1:I

    invoke-virtual {v1, v12}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v12

    if-eqz v12, :cond_6

    .line 37
    sget v12, Ld/i;->H1:I

    invoke-virtual {v1, v12, v10}, Landroidx/appcompat/widget/K;->a(IZ)Z

    move-result v12

    const/4 v13, 0x1

    goto :goto_0

    :cond_6
    move v12, v10

    move v13, v12

    .line 38
    :goto_0
    invoke-direct {v0, v8, v1}, Landroidx/appcompat/widget/o;->C(Landroid/content/Context;Landroidx/appcompat/widget/K;)V

    .line 39
    sget v14, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 40
    sget v15, Ld/i;->I1:I

    invoke-virtual {v1, v15}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v15

    if-eqz v15, :cond_7

    .line 41
    sget v15, Ld/i;->I1:I

    invoke-virtual {v1, v15}, Landroidx/appcompat/widget/K;->m(I)Ljava/lang/String;

    move-result-object v15

    goto :goto_1

    :cond_7
    const/4 v15, 0x0

    :goto_1
    if-lt v14, v3, :cond_8

    .line 42
    sget v14, Ld/i;->G1:I

    .line 43
    invoke-virtual {v1, v14}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v14

    if-eqz v14, :cond_8

    .line 44
    sget v14, Ld/i;->G1:I

    invoke-virtual {v1, v14}, Landroidx/appcompat/widget/K;->m(I)Ljava/lang/String;

    move-result-object v14

    goto :goto_2

    :cond_8
    const/4 v14, 0x0

    .line 45
    :goto_2
    invoke-virtual {v1}, Landroidx/appcompat/widget/K;->u()V

    goto :goto_3

    :cond_9
    move v12, v10

    move v13, v12

    const/4 v14, 0x0

    const/4 v15, 0x0

    .line 46
    :goto_3
    sget-object v1, Ld/i;->z1:[I

    invoke-static {v8, v4, v1, v6, v10}, Landroidx/appcompat/widget/K;->s(Landroid/content/Context;Landroid/util/AttributeSet;[III)Landroidx/appcompat/widget/K;

    move-result-object v1

    if-nez v2, :cond_a

    .line 47
    sget v5, Ld/i;->H1:I

    invoke-virtual {v1, v5}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v5

    if-eqz v5, :cond_a

    .line 48
    sget v5, Ld/i;->H1:I

    invoke-virtual {v1, v5, v10}, Landroidx/appcompat/widget/K;->a(IZ)Z

    move-result v12

    const/4 v5, 0x1

    goto :goto_4

    :cond_a
    move v5, v13

    .line 49
    :goto_4
    sget v13, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 50
    sget v11, Ld/i;->I1:I

    invoke-virtual {v1, v11}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v11

    if-eqz v11, :cond_b

    .line 51
    sget v11, Ld/i;->I1:I

    invoke-virtual {v1, v11}, Landroidx/appcompat/widget/K;->m(I)Ljava/lang/String;

    move-result-object v15

    :cond_b
    if-lt v13, v3, :cond_c

    .line 52
    sget v3, Ld/i;->G1:I

    .line 53
    invoke-virtual {v1, v3}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v3

    if-eqz v3, :cond_c

    .line 54
    sget v3, Ld/i;->G1:I

    invoke-virtual {v1, v3}, Landroidx/appcompat/widget/K;->m(I)Ljava/lang/String;

    move-result-object v14

    :cond_c
    const/16 v3, 0x1c

    if-lt v13, v3, :cond_d

    .line 55
    sget v3, Ld/i;->A1:I

    .line 56
    invoke-virtual {v1, v3}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v3

    if-eqz v3, :cond_d

    .line 57
    sget v3, Ld/i;->A1:I

    invoke-virtual {v1, v3, v7}, Landroidx/appcompat/widget/K;->e(II)I

    move-result v3

    if-nez v3, :cond_d

    .line 58
    iget-object v3, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    const/4 v11, 0x0

    invoke-virtual {v3, v10, v11}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 59
    :cond_d
    invoke-direct {v0, v8, v1}, Landroidx/appcompat/widget/o;->C(Landroid/content/Context;Landroidx/appcompat/widget/K;)V

    .line 60
    invoke-virtual {v1}, Landroidx/appcompat/widget/K;->u()V

    if-nez v2, :cond_e

    if-eqz v5, :cond_e

    .line 61
    invoke-virtual {v0, v12}, Landroidx/appcompat/widget/o;->s(Z)V

    .line 62
    :cond_e
    iget-object v1, v0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    if-eqz v1, :cond_10

    .line 63
    iget v2, v0, Landroidx/appcompat/widget/o;->k:I

    if-ne v2, v7, :cond_f

    .line 64
    iget-object v2, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    iget v3, v0, Landroidx/appcompat/widget/o;->j:I

    invoke-virtual {v2, v1, v3}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    goto :goto_5

    .line 65
    :cond_f
    iget-object v2, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-virtual {v2, v1}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;)V

    :cond_10
    :goto_5
    if-eqz v14, :cond_11

    .line 66
    iget-object v1, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-static {v1, v14}, Landroidx/appcompat/widget/o$d;->d(Landroid/widget/TextView;Ljava/lang/String;)Z

    :cond_11
    if-eqz v15, :cond_12

    .line 67
    iget-object v1, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-static {v15}, Landroidx/appcompat/widget/o$c;->a(Ljava/lang/String;)Landroid/os/LocaleList;

    move-result-object v2

    invoke-static {v1, v2}, Landroidx/appcompat/widget/o$c;->b(Landroid/widget/TextView;Landroid/os/LocaleList;)V

    .line 68
    :cond_12
    iget-object v1, v0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    invoke-virtual {v1, v4, v6}, Landroidx/appcompat/widget/q;->o(Landroid/util/AttributeSet;I)V

    .line 69
    sget-boolean v1, Landroidx/appcompat/widget/W;->a:Z

    const/high16 v11, -0x40800000    # -1.0f

    if-eqz v1, :cond_14

    .line 70
    iget-object v1, v0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    invoke-virtual {v1}, Landroidx/appcompat/widget/q;->j()I

    move-result v1

    if-eqz v1, :cond_14

    .line 71
    iget-object v1, v0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 72
    invoke-virtual {v1}, Landroidx/appcompat/widget/q;->i()[I

    move-result-object v1

    .line 73
    array-length v2, v1

    if-lez v2, :cond_14

    .line 74
    iget-object v2, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-static {v2}, Landroidx/appcompat/widget/o$d;->a(Landroid/widget/TextView;)I

    move-result v2

    int-to-float v2, v2

    cmpl-float v2, v2, v11

    if-eqz v2, :cond_13

    .line 75
    iget-object v1, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    iget-object v2, v0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 76
    invoke-virtual {v2}, Landroidx/appcompat/widget/q;->g()I

    move-result v2

    iget-object v3, v0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 77
    invoke-virtual {v3}, Landroidx/appcompat/widget/q;->f()I

    move-result v3

    iget-object v5, v0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 78
    invoke-virtual {v5}, Landroidx/appcompat/widget/q;->h()I

    move-result v5

    .line 79
    invoke-static {v1, v2, v3, v5, v10}, Landroidx/appcompat/widget/o$d;->b(Landroid/widget/TextView;IIII)V

    goto :goto_6

    .line 80
    :cond_13
    iget-object v2, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-static {v2, v1, v10}, Landroidx/appcompat/widget/o$d;->c(Landroid/widget/TextView;[II)V

    .line 81
    :cond_14
    :goto_6
    sget-object v1, Ld/i;->S:[I

    invoke-static {v8, v4, v1}, Landroidx/appcompat/widget/K;->r(Landroid/content/Context;Landroid/util/AttributeSet;[I)Landroidx/appcompat/widget/K;

    move-result-object v10

    .line 82
    sget v1, Ld/i;->a0:I

    invoke-virtual {v10, v1, v7}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v1

    if-eq v1, v7, :cond_15

    .line 83
    invoke-virtual {v9, v8, v1}, Landroidx/appcompat/widget/f;->c(Landroid/content/Context;I)Landroid/graphics/drawable/Drawable;

    move-result-object v1

    goto :goto_7

    :cond_15
    const/4 v1, 0x0

    .line 84
    :goto_7
    sget v2, Ld/i;->f0:I

    invoke-virtual {v10, v2, v7}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v2

    if-eq v2, v7, :cond_16

    .line 85
    invoke-virtual {v9, v8, v2}, Landroidx/appcompat/widget/f;->c(Landroid/content/Context;I)Landroid/graphics/drawable/Drawable;

    move-result-object v2

    goto :goto_8

    :cond_16
    const/4 v2, 0x0

    .line 86
    :goto_8
    sget v3, Ld/i;->b0:I

    invoke-virtual {v10, v3, v7}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v3

    if-eq v3, v7, :cond_17

    .line 87
    invoke-virtual {v9, v8, v3}, Landroidx/appcompat/widget/f;->c(Landroid/content/Context;I)Landroid/graphics/drawable/Drawable;

    move-result-object v3

    goto :goto_9

    :cond_17
    const/4 v3, 0x0

    .line 88
    :goto_9
    sget v4, Ld/i;->Y:I

    invoke-virtual {v10, v4, v7}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v4

    if-eq v4, v7, :cond_18

    .line 89
    invoke-virtual {v9, v8, v4}, Landroidx/appcompat/widget/f;->c(Landroid/content/Context;I)Landroid/graphics/drawable/Drawable;

    move-result-object v4

    goto :goto_a

    :cond_18
    const/4 v4, 0x0

    .line 90
    :goto_a
    sget v5, Ld/i;->c0:I

    invoke-virtual {v10, v5, v7}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v5

    if-eq v5, v7, :cond_19

    .line 91
    invoke-virtual {v9, v8, v5}, Landroidx/appcompat/widget/f;->c(Landroid/content/Context;I)Landroid/graphics/drawable/Drawable;

    move-result-object v5

    goto :goto_b

    :cond_19
    const/4 v5, 0x0

    .line 92
    :goto_b
    sget v6, Ld/i;->Z:I

    invoke-virtual {v10, v6, v7}, Landroidx/appcompat/widget/K;->l(II)I

    move-result v6

    if-eq v6, v7, :cond_1a

    .line 93
    invoke-virtual {v9, v8, v6}, Landroidx/appcompat/widget/f;->c(Landroid/content/Context;I)Landroid/graphics/drawable/Drawable;

    move-result-object v6

    goto :goto_c

    :cond_1a
    const/4 v6, 0x0

    .line 94
    :goto_c
    invoke-direct/range {v0 .. v6}, Landroidx/appcompat/widget/o;->y(Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;Landroid/graphics/drawable/Drawable;)V

    .line 95
    sget v1, Ld/i;->d0:I

    invoke-virtual {v10, v1}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v1

    if-eqz v1, :cond_1b

    .line 96
    sget v1, Ld/i;->d0:I

    invoke-virtual {v10, v1}, Landroidx/appcompat/widget/K;->c(I)Landroid/content/res/ColorStateList;

    move-result-object v1

    .line 97
    iget-object v2, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-static {v2, v1}, Landroidx/core/widget/f;->f(Landroid/widget/TextView;Landroid/content/res/ColorStateList;)V

    .line 98
    :cond_1b
    sget v1, Ld/i;->e0:I

    invoke-virtual {v10, v1}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v1

    if-eqz v1, :cond_1c

    .line 99
    sget v1, Ld/i;->e0:I

    .line 100
    invoke-virtual {v10, v1, v7}, Landroidx/appcompat/widget/K;->i(II)I

    move-result v1

    const/4 v2, 0x0

    .line 101
    invoke-static {v1, v2}, Landroidx/appcompat/widget/u;->c(ILandroid/graphics/PorterDuff$Mode;)Landroid/graphics/PorterDuff$Mode;

    move-result-object v1

    .line 102
    iget-object v2, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-static {v2, v1}, Landroidx/core/widget/f;->g(Landroid/widget/TextView;Landroid/graphics/PorterDuff$Mode;)V

    .line 103
    :cond_1c
    sget v1, Ld/i;->h0:I

    invoke-virtual {v10, v1, v7}, Landroidx/appcompat/widget/K;->e(II)I

    move-result v1

    .line 104
    sget v2, Ld/i;->i0:I

    invoke-virtual {v10, v2, v7}, Landroidx/appcompat/widget/K;->e(II)I

    move-result v2

    .line 105
    sget v3, Ld/i;->j0:I

    invoke-virtual {v10, v3}, Landroidx/appcompat/widget/K;->p(I)Z

    move-result v3

    if-eqz v3, :cond_1e

    .line 106
    sget v3, Ld/i;->j0:I

    invoke-virtual {v10, v3}, Landroidx/appcompat/widget/K;->t(I)Landroid/util/TypedValue;

    move-result-object v3

    if-eqz v3, :cond_1d

    .line 107
    iget v4, v3, Landroid/util/TypedValue;->type:I

    const/4 v5, 0x5

    if-ne v4, v5, :cond_1d

    .line 108
    iget v4, v3, Landroid/util/TypedValue;->data:I

    invoke-static {v4}, Lx/e;->a(I)I

    move-result v4

    .line 109
    iget v3, v3, Landroid/util/TypedValue;->data:I

    invoke-static {v3}, Landroid/util/TypedValue;->complexToFloat(I)F

    move-result v3

    goto :goto_d

    .line 110
    :cond_1d
    sget v3, Ld/i;->j0:I

    invoke-virtual {v10, v3, v7}, Landroidx/appcompat/widget/K;->e(II)I

    move-result v3

    int-to-float v3, v3

    move v4, v7

    goto :goto_d

    :cond_1e
    move v4, v7

    move v3, v11

    .line 111
    :goto_d
    invoke-virtual {v10}, Landroidx/appcompat/widget/K;->u()V

    if-eq v1, v7, :cond_1f

    .line 112
    iget-object v5, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-static {v5, v1}, Landroidx/core/widget/f;->h(Landroid/widget/TextView;I)V

    :cond_1f
    if-eq v2, v7, :cond_20

    .line 113
    iget-object v1, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-static {v1, v2}, Landroidx/core/widget/f;->i(Landroid/widget/TextView;I)V

    :cond_20
    cmpl-float v1, v3, v11

    if-eqz v1, :cond_22

    if-ne v4, v7, :cond_21

    .line 114
    iget-object v1, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    float-to-int v2, v3

    invoke-static {v1, v2}, Landroidx/core/widget/f;->j(Landroid/widget/TextView;I)V

    return-void

    .line 115
    :cond_21
    iget-object v1, v0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    invoke-static {v1, v4, v3}, Landroidx/core/widget/f;->k(Landroid/widget/TextView;IF)V

    :cond_22
    return-void
.end method

.method n(Ljava/lang/ref/WeakReference;Landroid/graphics/Typeface;)V
    .locals 2

    .line 1
    iget-boolean v0, p0, Landroidx/appcompat/widget/o;->m:Z

    .line 2
    .line 3
    if-eqz v0, :cond_1

    .line 4
    .line 5
    iput-object p2, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 6
    .line 7
    invoke-virtual {p1}, Ljava/lang/ref/Reference;->get()Ljava/lang/Object;

    .line 8
    .line 9
    .line 10
    move-result-object p1

    .line 11
    check-cast p1, Landroid/widget/TextView;

    .line 12
    .line 13
    if-eqz p1, :cond_1

    .line 14
    .line 15
    invoke-virtual {p1}, Landroid/view/View;->isAttachedToWindow()Z

    .line 16
    .line 17
    .line 18
    move-result v0

    .line 19
    if-eqz v0, :cond_0

    .line 20
    .line 21
    iget v0, p0, Landroidx/appcompat/widget/o;->j:I

    .line 22
    .line 23
    new-instance v1, Landroidx/appcompat/widget/o$b;

    .line 24
    .line 25
    invoke-direct {v1, p0, p1, p2, v0}, Landroidx/appcompat/widget/o$b;-><init>(Landroidx/appcompat/widget/o;Landroid/widget/TextView;Landroid/graphics/Typeface;I)V

    .line 26
    .line 27
    .line 28
    invoke-virtual {p1, v1}, Landroid/view/View;->post(Ljava/lang/Runnable;)Z

    .line 29
    .line 30
    .line 31
    return-void

    .line 32
    :cond_0
    iget v0, p0, Landroidx/appcompat/widget/o;->j:I

    .line 33
    .line 34
    invoke-virtual {p1, p2, v0}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 35
    .line 36
    .line 37
    :cond_1
    return-void
.end method

.method o(ZIIII)V
    .locals 0

    .line 1
    sget-boolean p1, Landroidx/appcompat/widget/W;->a:Z

    .line 2
    .line 3
    if-nez p1, :cond_0

    .line 4
    .line 5
    invoke-virtual {p0}, Landroidx/appcompat/widget/o;->c()V

    .line 6
    .line 7
    .line 8
    :cond_0
    return-void
.end method

.method p()V
    .locals 0

    .line 1
    invoke-virtual {p0}, Landroidx/appcompat/widget/o;->b()V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method q(Landroid/content/Context;I)V
    .locals 4

    .line 1
    sget-object v0, Ld/i;->z1:[I

    .line 2
    .line 3
    invoke-static {p1, p2, v0}, Landroidx/appcompat/widget/K;->q(Landroid/content/Context;I[I)Landroidx/appcompat/widget/K;

    .line 4
    .line 5
    .line 6
    move-result-object p2

    .line 7
    sget v0, Ld/i;->H1:I

    .line 8
    .line 9
    invoke-virtual {p2, v0}, Landroidx/appcompat/widget/K;->p(I)Z

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
    sget v0, Ld/i;->H1:I

    .line 17
    .line 18
    invoke-virtual {p2, v0, v1}, Landroidx/appcompat/widget/K;->a(IZ)Z

    .line 19
    .line 20
    .line 21
    move-result v0

    .line 22
    invoke-virtual {p0, v0}, Landroidx/appcompat/widget/o;->s(Z)V

    .line 23
    .line 24
    .line 25
    :cond_0
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 26
    .line 27
    sget v2, Ld/i;->A1:I

    .line 28
    .line 29
    invoke-virtual {p2, v2}, Landroidx/appcompat/widget/K;->p(I)Z

    .line 30
    .line 31
    .line 32
    move-result v2

    .line 33
    if-eqz v2, :cond_1

    .line 34
    .line 35
    sget v2, Ld/i;->A1:I

    .line 36
    .line 37
    const/4 v3, -0x1

    .line 38
    invoke-virtual {p2, v2, v3}, Landroidx/appcompat/widget/K;->e(II)I

    .line 39
    .line 40
    .line 41
    move-result v2

    .line 42
    if-nez v2, :cond_1

    .line 43
    .line 44
    iget-object v2, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 45
    .line 46
    const/4 v3, 0x0

    .line 47
    invoke-virtual {v2, v1, v3}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 48
    .line 49
    .line 50
    :cond_1
    invoke-direct {p0, p1, p2}, Landroidx/appcompat/widget/o;->C(Landroid/content/Context;Landroidx/appcompat/widget/K;)V

    .line 51
    .line 52
    .line 53
    const/16 p1, 0x1a

    .line 54
    .line 55
    if-lt v0, p1, :cond_2

    .line 56
    .line 57
    sget p1, Ld/i;->G1:I

    .line 58
    .line 59
    invoke-virtual {p2, p1}, Landroidx/appcompat/widget/K;->p(I)Z

    .line 60
    .line 61
    .line 62
    move-result p1

    .line 63
    if-eqz p1, :cond_2

    .line 64
    .line 65
    sget p1, Ld/i;->G1:I

    .line 66
    .line 67
    invoke-virtual {p2, p1}, Landroidx/appcompat/widget/K;->m(I)Ljava/lang/String;

    .line 68
    .line 69
    .line 70
    move-result-object p1

    .line 71
    if-eqz p1, :cond_2

    .line 72
    .line 73
    iget-object v0, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 74
    .line 75
    invoke-static {v0, p1}, Landroidx/appcompat/widget/o$d;->d(Landroid/widget/TextView;Ljava/lang/String;)Z

    .line 76
    .line 77
    .line 78
    :cond_2
    invoke-virtual {p2}, Landroidx/appcompat/widget/K;->u()V

    .line 79
    .line 80
    .line 81
    iget-object p1, p0, Landroidx/appcompat/widget/o;->l:Landroid/graphics/Typeface;

    .line 82
    .line 83
    if-eqz p1, :cond_3

    .line 84
    .line 85
    iget-object p2, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 86
    .line 87
    iget v0, p0, Landroidx/appcompat/widget/o;->j:I

    .line 88
    .line 89
    invoke-virtual {p2, p1, v0}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 90
    .line 91
    .line 92
    :cond_3
    return-void
.end method

.method r(Landroid/widget/TextView;Landroid/view/inputmethod/InputConnection;Landroid/view/inputmethod/EditorInfo;)V
    .locals 2

    .line 1
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 2
    .line 3
    const/16 v1, 0x1e

    .line 4
    .line 5
    if-ge v0, v1, :cond_0

    .line 6
    .line 7
    if-eqz p2, :cond_0

    .line 8
    .line 9
    invoke-virtual {p1}, Landroid/widget/TextView;->getText()Ljava/lang/CharSequence;

    .line 10
    .line 11
    .line 12
    move-result-object p1

    .line 13
    invoke-static {p3, p1}, LB/a;->d(Landroid/view/inputmethod/EditorInfo;Ljava/lang/CharSequence;)V

    .line 14
    .line 15
    .line 16
    :cond_0
    return-void
.end method

.method s(Z)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->a:Landroid/widget/TextView;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Landroid/widget/TextView;->setAllCaps(Z)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method t(IIII)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0, p1, p2, p3, p4}, Landroidx/appcompat/widget/q;->p(IIII)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method u([II)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0, p1, p2}, Landroidx/appcompat/widget/q;->q([II)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method v(I)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->i:Landroidx/appcompat/widget/q;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Landroidx/appcompat/widget/q;->r(I)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method w(Landroid/content/res/ColorStateList;)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->h:Landroidx/appcompat/widget/I;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    new-instance v0, Landroidx/appcompat/widget/I;

    .line 6
    .line 7
    invoke-direct {v0}, Landroidx/appcompat/widget/I;-><init>()V

    .line 8
    .line 9
    .line 10
    iput-object v0, p0, Landroidx/appcompat/widget/o;->h:Landroidx/appcompat/widget/I;

    .line 11
    .line 12
    :cond_0
    iget-object v0, p0, Landroidx/appcompat/widget/o;->h:Landroidx/appcompat/widget/I;

    .line 13
    .line 14
    iput-object p1, v0, Landroidx/appcompat/widget/I;->a:Landroid/content/res/ColorStateList;

    .line 15
    .line 16
    if-eqz p1, :cond_1

    .line 17
    .line 18
    const/4 p1, 0x1

    .line 19
    goto :goto_0

    .line 20
    :cond_1
    const/4 p1, 0x0

    .line 21
    :goto_0
    iput-boolean p1, v0, Landroidx/appcompat/widget/I;->d:Z

    .line 22
    .line 23
    invoke-direct {p0}, Landroidx/appcompat/widget/o;->z()V

    .line 24
    .line 25
    .line 26
    return-void
.end method

.method x(Landroid/graphics/PorterDuff$Mode;)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/o;->h:Landroidx/appcompat/widget/I;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    new-instance v0, Landroidx/appcompat/widget/I;

    .line 6
    .line 7
    invoke-direct {v0}, Landroidx/appcompat/widget/I;-><init>()V

    .line 8
    .line 9
    .line 10
    iput-object v0, p0, Landroidx/appcompat/widget/o;->h:Landroidx/appcompat/widget/I;

    .line 11
    .line 12
    :cond_0
    iget-object v0, p0, Landroidx/appcompat/widget/o;->h:Landroidx/appcompat/widget/I;

    .line 13
    .line 14
    iput-object p1, v0, Landroidx/appcompat/widget/I;->b:Landroid/graphics/PorterDuff$Mode;

    .line 15
    .line 16
    if-eqz p1, :cond_1

    .line 17
    .line 18
    const/4 p1, 0x1

    .line 19
    goto :goto_0

    .line 20
    :cond_1
    const/4 p1, 0x0

    .line 21
    :goto_0
    iput-boolean p1, v0, Landroidx/appcompat/widget/I;->c:Z

    .line 22
    .line 23
    invoke-direct {p0}, Landroidx/appcompat/widget/o;->z()V

    .line 24
    .line 25
    .line 26
    return-void
.end method
