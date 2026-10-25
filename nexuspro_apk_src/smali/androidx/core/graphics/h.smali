.class public abstract Landroidx/core/graphics/h;
.super Ljava/lang/Object;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Landroidx/core/graphics/h$a;
    }
.end annotation


# static fields
.field private static final a:Landroidx/core/graphics/n;

.field private static final b:Lq/h;


# direct methods
.method static constructor <clinit>()V
    .locals 2

    .line 1
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 2
    .line 3
    const/16 v1, 0x1d

    .line 4
    .line 5
    if-lt v0, v1, :cond_0

    .line 6
    .line 7
    new-instance v0, Landroidx/core/graphics/m;

    .line 8
    .line 9
    invoke-direct {v0}, Landroidx/core/graphics/m;-><init>()V

    .line 10
    .line 11
    .line 12
    sput-object v0, Landroidx/core/graphics/h;->a:Landroidx/core/graphics/n;

    .line 13
    .line 14
    goto :goto_0

    .line 15
    :cond_0
    const/16 v1, 0x1c

    .line 16
    .line 17
    if-lt v0, v1, :cond_1

    .line 18
    .line 19
    new-instance v0, Landroidx/core/graphics/l;

    .line 20
    .line 21
    invoke-direct {v0}, Landroidx/core/graphics/l;-><init>()V

    .line 22
    .line 23
    .line 24
    sput-object v0, Landroidx/core/graphics/h;->a:Landroidx/core/graphics/n;

    .line 25
    .line 26
    goto :goto_0

    .line 27
    :cond_1
    const/16 v1, 0x1a

    .line 28
    .line 29
    if-lt v0, v1, :cond_2

    .line 30
    .line 31
    new-instance v0, Landroidx/core/graphics/k;

    .line 32
    .line 33
    invoke-direct {v0}, Landroidx/core/graphics/k;-><init>()V

    .line 34
    .line 35
    .line 36
    sput-object v0, Landroidx/core/graphics/h;->a:Landroidx/core/graphics/n;

    .line 37
    .line 38
    goto :goto_0

    .line 39
    :cond_2
    invoke-static {}, Landroidx/core/graphics/j;->j()Z

    .line 40
    .line 41
    .line 42
    move-result v0

    .line 43
    if-eqz v0, :cond_3

    .line 44
    .line 45
    new-instance v0, Landroidx/core/graphics/j;

    .line 46
    .line 47
    invoke-direct {v0}, Landroidx/core/graphics/j;-><init>()V

    .line 48
    .line 49
    .line 50
    sput-object v0, Landroidx/core/graphics/h;->a:Landroidx/core/graphics/n;

    .line 51
    .line 52
    goto :goto_0

    .line 53
    :cond_3
    new-instance v0, Landroidx/core/graphics/i;

    .line 54
    .line 55
    invoke-direct {v0}, Landroidx/core/graphics/i;-><init>()V

    .line 56
    .line 57
    .line 58
    sput-object v0, Landroidx/core/graphics/h;->a:Landroidx/core/graphics/n;

    .line 59
    .line 60
    :goto_0
    new-instance v0, Lq/h;

    .line 61
    .line 62
    const/16 v1, 0x10

    .line 63
    .line 64
    invoke-direct {v0, v1}, Lq/h;-><init>(I)V

    .line 65
    .line 66
    .line 67
    sput-object v0, Landroidx/core/graphics/h;->b:Lq/h;

    .line 68
    .line 69
    return-void
.end method

.method public static a(Landroid/content/Context;Landroid/graphics/Typeface;I)Landroid/graphics/Typeface;
    .locals 0

    .line 1
    if-eqz p0, :cond_0

    .line 2
    .line 3
    invoke-static {p1, p2}, Landroid/graphics/Typeface;->create(Landroid/graphics/Typeface;I)Landroid/graphics/Typeface;

    .line 4
    .line 5
    .line 6
    move-result-object p0

    .line 7
    return-object p0

    .line 8
    :cond_0
    new-instance p0, Ljava/lang/IllegalArgumentException;

    .line 9
    .line 10
    const-string p1, "Context cannot be null"

    .line 11
    .line 12
    invoke-direct {p0, p1}, Ljava/lang/IllegalArgumentException;-><init>(Ljava/lang/String;)V

    .line 13
    .line 14
    .line 15
    throw p0
.end method

.method public static b(Landroid/content/Context;Landroid/os/CancellationSignal;[Lv/g$b;I)Landroid/graphics/Typeface;
    .locals 1

    .line 1
    sget-object v0, Landroidx/core/graphics/h;->a:Landroidx/core/graphics/n;

    .line 2
    .line 3
    invoke-virtual {v0, p0, p1, p2, p3}, Landroidx/core/graphics/n;->b(Landroid/content/Context;Landroid/os/CancellationSignal;[Lv/g$b;I)Landroid/graphics/Typeface;

    .line 4
    .line 5
    .line 6
    move-result-object p0

    .line 7
    return-object p0
.end method

.method public static c(Landroid/content/Context;Landroidx/core/content/res/d$b;Landroid/content/res/Resources;ILjava/lang/String;IILandroidx/core/content/res/f$e;Landroid/os/Handler;Z)Landroid/graphics/Typeface;
    .locals 12

    move-object/from16 v0, p7

    move-object/from16 v1, p8

    .line 1
    instance-of v2, p1, Landroidx/core/content/res/d$e;

    if-eqz v2, :cond_5

    .line 2
    check-cast p1, Landroidx/core/content/res/d$e;

    .line 3
    invoke-virtual {p1}, Landroidx/core/content/res/d$e;->c()Ljava/lang/String;

    move-result-object v2

    .line 4
    invoke-static {v2}, Landroidx/core/graphics/h;->g(Ljava/lang/String;)Landroid/graphics/Typeface;

    move-result-object v2

    if-eqz v2, :cond_1

    if-eqz v0, :cond_0

    .line 5
    invoke-virtual {v0, v2, v1}, Landroidx/core/content/res/f$e;->d(Landroid/graphics/Typeface;Landroid/os/Handler;)V

    :cond_0
    return-object v2

    :cond_1
    const/4 v2, 0x0

    const/4 v3, 0x1

    if-eqz p9, :cond_3

    .line 6
    invoke-virtual {p1}, Landroidx/core/content/res/d$e;->a()I

    move-result v4

    if-nez v4, :cond_2

    :goto_0
    move v8, v3

    goto :goto_1

    :cond_2
    move v8, v2

    goto :goto_1

    :cond_3
    if-nez v0, :cond_2

    goto :goto_0

    :goto_1
    if-eqz p9, :cond_4

    .line 7
    invoke-virtual {p1}, Landroidx/core/content/res/d$e;->d()I

    move-result v2

    :goto_2
    move v9, v2

    goto :goto_3

    :cond_4
    const/4 v2, -0x1

    goto :goto_2

    .line 8
    :goto_3
    invoke-static {v1}, Landroidx/core/content/res/f$e;->e(Landroid/os/Handler;)Landroid/os/Handler;

    move-result-object v10

    .line 9
    new-instance v11, Landroidx/core/graphics/h$a;

    invoke-direct {v11, v0}, Landroidx/core/graphics/h$a;-><init>(Landroidx/core/content/res/f$e;)V

    .line 10
    invoke-virtual {p1}, Landroidx/core/content/res/d$e;->b()Lv/e;

    move-result-object v6

    move-object v5, p0

    move/from16 v7, p6

    invoke-static/range {v5 .. v11}, Lv/g;->c(Landroid/content/Context;Lv/e;IZILandroid/os/Handler;Lv/g$c;)Landroid/graphics/Typeface;

    move-result-object p0

    goto :goto_4

    .line 11
    :cond_5
    sget-object v2, Landroidx/core/graphics/h;->a:Landroidx/core/graphics/n;

    check-cast p1, Landroidx/core/content/res/d$c;

    move/from16 v7, p6

    invoke-virtual {v2, p0, p1, p2, v7}, Landroidx/core/graphics/n;->a(Landroid/content/Context;Landroidx/core/content/res/d$c;Landroid/content/res/Resources;I)Landroid/graphics/Typeface;

    move-result-object p0

    if-eqz v0, :cond_7

    if-eqz p0, :cond_6

    .line 12
    invoke-virtual {v0, p0, v1}, Landroidx/core/content/res/f$e;->d(Landroid/graphics/Typeface;Landroid/os/Handler;)V

    goto :goto_4

    :cond_6
    const/4 p1, -0x3

    .line 13
    invoke-virtual {v0, p1, v1}, Landroidx/core/content/res/f$e;->c(ILandroid/os/Handler;)V

    :cond_7
    :goto_4
    if-eqz p0, :cond_8

    .line 14
    sget-object p1, Landroidx/core/graphics/h;->b:Lq/h;

    invoke-static/range {p2 .. p6}, Landroidx/core/graphics/h;->e(Landroid/content/res/Resources;ILjava/lang/String;II)Ljava/lang/String;

    move-result-object p2

    invoke-virtual {p1, p2, p0}, Lq/h;->d(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    :cond_8
    return-object p0
.end method

.method public static d(Landroid/content/Context;Landroid/content/res/Resources;ILjava/lang/String;II)Landroid/graphics/Typeface;
    .locals 6

    .line 1
    sget-object v0, Landroidx/core/graphics/h;->a:Landroidx/core/graphics/n;

    .line 2
    .line 3
    move-object v1, p0

    .line 4
    move-object v2, p1

    .line 5
    move v3, p2

    .line 6
    move-object v4, p3

    .line 7
    move v5, p5

    .line 8
    invoke-virtual/range {v0 .. v5}, Landroidx/core/graphics/n;->d(Landroid/content/Context;Landroid/content/res/Resources;ILjava/lang/String;I)Landroid/graphics/Typeface;

    .line 9
    .line 10
    .line 11
    move-result-object p0

    .line 12
    if-eqz p0, :cond_0

    .line 13
    .line 14
    invoke-static {v2, v3, v4, p4, v5}, Landroidx/core/graphics/h;->e(Landroid/content/res/Resources;ILjava/lang/String;II)Ljava/lang/String;

    .line 15
    .line 16
    .line 17
    move-result-object p1

    .line 18
    sget-object p2, Landroidx/core/graphics/h;->b:Lq/h;

    .line 19
    .line 20
    invoke-virtual {p2, p1, p0}, Lq/h;->d(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 21
    .line 22
    .line 23
    :cond_0
    return-object p0
.end method

.method private static e(Landroid/content/res/Resources;ILjava/lang/String;II)Ljava/lang/String;
    .locals 1

    .line 1
    new-instance v0, Ljava/lang/StringBuilder;

    .line 2
    .line 3
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    .line 4
    .line 5
    .line 6
    invoke-virtual {p0, p1}, Landroid/content/res/Resources;->getResourcePackageName(I)Ljava/lang/String;

    .line 7
    .line 8
    .line 9
    move-result-object p0

    .line 10
    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 11
    .line 12
    .line 13
    const/16 p0, 0x2d

    .line 14
    .line 15
    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 16
    .line 17
    .line 18
    invoke-virtual {v0, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 19
    .line 20
    .line 21
    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 22
    .line 23
    .line 24
    invoke-virtual {v0, p3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    .line 25
    .line 26
    .line 27
    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 28
    .line 29
    .line 30
    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    .line 31
    .line 32
    .line 33
    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 34
    .line 35
    .line 36
    invoke-virtual {v0, p4}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    .line 37
    .line 38
    .line 39
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 40
    .line 41
    .line 42
    move-result-object p0

    .line 43
    return-object p0
.end method

.method public static f(Landroid/content/res/Resources;ILjava/lang/String;II)Landroid/graphics/Typeface;
    .locals 1

    .line 1
    sget-object v0, Landroidx/core/graphics/h;->b:Lq/h;

    .line 2
    .line 3
    invoke-static {p0, p1, p2, p3, p4}, Landroidx/core/graphics/h;->e(Landroid/content/res/Resources;ILjava/lang/String;II)Ljava/lang/String;

    .line 4
    .line 5
    .line 6
    move-result-object p0

    .line 7
    invoke-virtual {v0, p0}, Lq/h;->c(Ljava/lang/Object;)Ljava/lang/Object;

    .line 8
    .line 9
    .line 10
    move-result-object p0

    .line 11
    check-cast p0, Landroid/graphics/Typeface;

    .line 12
    .line 13
    return-object p0
.end method

.method private static g(Ljava/lang/String;)Landroid/graphics/Typeface;
    .locals 3

    .line 1
    const/4 v0, 0x0

    .line 2
    if-eqz p0, :cond_1

    .line 3
    .line 4
    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    .line 5
    .line 6
    .line 7
    move-result v1

    .line 8
    if-eqz v1, :cond_0

    .line 9
    .line 10
    goto :goto_0

    .line 11
    :cond_0
    const/4 v1, 0x0

    .line 12
    invoke-static {p0, v1}, Landroid/graphics/Typeface;->create(Ljava/lang/String;I)Landroid/graphics/Typeface;

    .line 13
    .line 14
    .line 15
    move-result-object p0

    .line 16
    sget-object v2, Landroid/graphics/Typeface;->DEFAULT:Landroid/graphics/Typeface;

    .line 17
    .line 18
    invoke-static {v2, v1}, Landroid/graphics/Typeface;->create(Landroid/graphics/Typeface;I)Landroid/graphics/Typeface;

    .line 19
    .line 20
    .line 21
    move-result-object v1

    .line 22
    if-eqz p0, :cond_1

    .line 23
    .line 24
    invoke-virtual {p0, v1}, Landroid/graphics/Typeface;->equals(Ljava/lang/Object;)Z

    .line 25
    .line 26
    .line 27
    move-result v1

    .line 28
    if-nez v1, :cond_1

    .line 29
    .line 30
    return-object p0

    .line 31
    :cond_1
    :goto_0
    return-object v0
.end method
