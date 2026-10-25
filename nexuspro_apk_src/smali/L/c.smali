.class public LL/c;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements LL/e;


# static fields
.field private static o:LL/f;


# instance fields
.field private final a:Landroid/app/Activity;

.field private final b:I

.field private final c:I

.field private final d:Landroid/widget/ImageView$ScaleType;

.field private final e:Landroid/graphics/Matrix;

.field private final f:Ljava/lang/String;

.field private final g:I

.field private h:Landroid/graphics/Bitmap;

.field private i:LL/d;

.field private j:Ljava/lang/String;

.field private k:Z

.field private l:Z

.field private m:Ljava/lang/Runnable;

.field private n:Z


# direct methods
.method static constructor <clinit>()V
    .locals 1

    .line 1
    new-instance v0, LL/f;

    .line 2
    .line 3
    invoke-direct {v0}, LL/f;-><init>()V

    .line 4
    .line 5
    .line 6
    sput-object v0, LL/c;->o:LL/f;

    .line 7
    .line 8
    return-void
.end method

.method public constructor <init>(Landroid/app/Activity;IILandroid/widget/ImageView$ScaleType;Landroid/graphics/Matrix;ILjava/lang/String;Z)V
    .locals 1

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 2
    .line 3
    .line 4
    const/4 v0, 0x0

    .line 5
    iput-boolean v0, p0, LL/c;->l:Z

    .line 6
    .line 7
    iput p2, p0, LL/c;->b:I

    .line 8
    .line 9
    iput p3, p0, LL/c;->c:I

    .line 10
    .line 11
    iput-object p4, p0, LL/c;->d:Landroid/widget/ImageView$ScaleType;

    .line 12
    .line 13
    iput-object p5, p0, LL/c;->e:Landroid/graphics/Matrix;

    .line 14
    .line 15
    iput-object p1, p0, LL/c;->a:Landroid/app/Activity;

    .line 16
    .line 17
    iput-object p7, p0, LL/c;->f:Ljava/lang/String;

    .line 18
    .line 19
    iput p6, p0, LL/c;->g:I

    .line 20
    .line 21
    iput-boolean p8, p0, LL/c;->n:Z

    .line 22
    .line 23
    return-void
.end method

.method public static synthetic c(LL/c;Ljava/lang/Runnable;)V
    .locals 0

    .line 1
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    .line 2
    .line 3
    .line 4
    invoke-interface {p1}, Ljava/lang/Runnable;->run()V

    .line 5
    .line 6
    .line 7
    iget-object p0, p0, LL/c;->a:Landroid/app/Activity;

    .line 8
    .line 9
    const/4 p1, 0x0

    .line 10
    invoke-virtual {p0, p1, p1}, Landroid/app/Activity;->overridePendingTransition(II)V

    .line 11
    .line 12
    .line 13
    return-void
.end method

.method public static synthetic d(LL/c;Lo/q;Ljava/lang/Runnable;Ln/f;Z)V
    .locals 0

    .line 1
    invoke-direct {p0, p1, p4, p2, p3}, LL/c;->i(Lo/q;ZLjava/lang/Runnable;Ln/f;)V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method private e(Ljava/lang/String;Lo/q;)V
    .locals 2

    .line 1
    sget-object v0, LL/c;->o:LL/f;

    .line 2
    .line 3
    iget-object v1, p0, LL/c;->a:Landroid/app/Activity;

    .line 4
    .line 5
    invoke-virtual {v0, v1, p1, p2}, LL/f;->b(Landroid/content/Context;Ljava/lang/String;Lo/q;)Ljava/lang/Integer;

    .line 6
    .line 7
    .line 8
    move-result-object v0

    .line 9
    if-eqz v0, :cond_0

    .line 10
    .line 11
    iget-object v1, p0, LL/c;->a:Landroid/app/Activity;

    .line 12
    .line 13
    invoke-virtual {v0}, Ljava/lang/Integer;->intValue()I

    .line 14
    .line 15
    .line 16
    move-result v0

    .line 17
    invoke-static {v1, v0}, LK/L;->d(Landroid/app/Activity;I)V

    .line 18
    .line 19
    .line 20
    :cond_0
    sget-object v0, LL/c;->o:LL/f;

    .line 21
    .line 22
    iget-object v1, p0, LL/c;->a:Landroid/app/Activity;

    .line 23
    .line 24
    invoke-virtual {v0, v1, p1, p2}, LL/f;->c(Landroid/content/Context;Ljava/lang/String;Lo/q;)Ljava/lang/Integer;

    .line 25
    .line 26
    .line 27
    move-result-object p1

    .line 28
    if-eqz p1, :cond_1

    .line 29
    .line 30
    iget-object p2, p0, LL/c;->a:Landroid/app/Activity;

    .line 31
    .line 32
    invoke-virtual {p1}, Ljava/lang/Integer;->intValue()I

    .line 33
    .line 34
    .line 35
    move-result p1

    .line 36
    invoke-static {p2, p1}, LK/L;->e(Landroid/app/Activity;I)V

    .line 37
    .line 38
    .line 39
    :cond_1
    return-void
.end method

.method private g()Landroid/os/Bundle;
    .locals 3

    .line 1
    new-instance v0, Landroid/os/Bundle;

    .line 2
    .line 3
    invoke-direct {v0}, Landroid/os/Bundle;-><init>()V

    .line 4
    .line 5
    .line 6
    const-string v1, "androidx.browser.trusted.KEY_SPLASH_SCREEN_VERSION"

    .line 7
    .line 8
    const-string v2, "androidx.browser.trusted.category.TrustedWebActivitySplashScreensV1"

    .line 9
    .line 10
    invoke-virtual {v0, v1, v2}, Landroid/os/BaseBundle;->putString(Ljava/lang/String;Ljava/lang/String;)V

    .line 11
    .line 12
    .line 13
    const-string v1, "androidx.browser.trusted.KEY_SPLASH_SCREEN_FADE_OUT_DURATION"

    .line 14
    .line 15
    iget v2, p0, LL/c;->g:I

    .line 16
    .line 17
    invoke-virtual {v0, v1, v2}, Landroid/os/BaseBundle;->putInt(Ljava/lang/String;I)V

    .line 18
    .line 19
    .line 20
    const-string v1, "androidx.browser.trusted.trusted.KEY_SPLASH_SCREEN_BACKGROUND_COLOR"

    .line 21
    .line 22
    iget v2, p0, LL/c;->c:I

    .line 23
    .line 24
    invoke-virtual {v0, v1, v2}, Landroid/os/BaseBundle;->putInt(Ljava/lang/String;I)V

    .line 25
    .line 26
    .line 27
    iget-object v1, p0, LL/c;->d:Landroid/widget/ImageView$ScaleType;

    .line 28
    .line 29
    invoke-virtual {v1}, Ljava/lang/Enum;->ordinal()I

    .line 30
    .line 31
    .line 32
    move-result v1

    .line 33
    const-string v2, "androidx.browser.trusted.KEY_SPLASH_SCREEN_SCALE_TYPE"

    .line 34
    .line 35
    invoke-virtual {v0, v2, v1}, Landroid/os/BaseBundle;->putInt(Ljava/lang/String;I)V

    .line 36
    .line 37
    .line 38
    iget-object v1, p0, LL/c;->e:Landroid/graphics/Matrix;

    .line 39
    .line 40
    if-eqz v1, :cond_0

    .line 41
    .line 42
    const/16 v2, 0x9

    .line 43
    .line 44
    new-array v2, v2, [F

    .line 45
    .line 46
    invoke-virtual {v1, v2}, Landroid/graphics/Matrix;->getValues([F)V

    .line 47
    .line 48
    .line 49
    const-string v1, "androidx.browser.trusted.KEY_SPLASH_SCREEN_TRANSFORMATION_MATRIX"

    .line 50
    .line 51
    invoke-virtual {v0, v1, v2}, Landroid/os/Bundle;->putFloatArray(Ljava/lang/String;[F)V

    .line 52
    .line 53
    .line 54
    :cond_0
    return-object v0
.end method

.method private i(Lo/q;ZLjava/lang/Runnable;Ln/f;)V
    .locals 0

    .line 1
    if-nez p2, :cond_0

    .line 2
    .line 3
    const-string p1, "SplashScreenStrategy"

    .line 4
    .line 5
    const-string p2, "Failed to transfer splash image."

    .line 6
    .line 7
    invoke-static {p1, p2}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 8
    .line 9
    .line 10
    invoke-interface {p3}, Ljava/lang/Runnable;->run()V

    .line 11
    .line 12
    .line 13
    return-void

    .line 14
    :cond_0
    invoke-direct {p0}, LL/c;->g()Landroid/os/Bundle;

    .line 15
    .line 16
    .line 17
    move-result-object p2

    .line 18
    invoke-virtual {p1, p2}, Lo/q;->o(Landroid/os/Bundle;)Lo/q;

    .line 19
    .line 20
    .line 21
    new-instance p2, LL/b;

    .line 22
    .line 23
    invoke-direct {p2, p0, p3}, LL/b;-><init>(LL/c;Ljava/lang/Runnable;)V

    .line 24
    .line 25
    .line 26
    iget-boolean p3, p0, LL/c;->n:Z

    .line 27
    .line 28
    if-eqz p3, :cond_1

    .line 29
    .line 30
    invoke-interface {p2}, Ljava/lang/Runnable;->run()V

    .line 31
    .line 32
    .line 33
    return-void

    .line 34
    :cond_1
    invoke-virtual {p1}, Lo/q;->c()Landroid/net/Uri;

    .line 35
    .line 36
    .line 37
    move-result-object p1

    .line 38
    invoke-direct {p0, p2, p4, p1}, LL/c;->j(Ljava/lang/Runnable;Ln/f;Landroid/net/Uri;)V

    .line 39
    .line 40
    .line 41
    return-void
.end method

.method private j(Ljava/lang/Runnable;Ln/f;Landroid/net/Uri;)V
    .locals 1

    .line 1
    iget-boolean v0, p0, LL/c;->l:Z

    .line 2
    .line 3
    if-eqz v0, :cond_0

    .line 4
    .line 5
    invoke-interface {p1}, Ljava/lang/Runnable;->run()V

    .line 6
    .line 7
    .line 8
    return-void

    .line 9
    :cond_0
    iput-object p1, p0, LL/c;->m:Ljava/lang/Runnable;

    .line 10
    .line 11
    const/4 p1, 0x0

    .line 12
    invoke-virtual {p2, p3, p1, p1}, Ln/f;->f(Landroid/net/Uri;Landroid/os/Bundle;Ljava/util/List;)Z

    .line 13
    .line 14
    .line 15
    move-result p1

    .line 16
    new-instance p2, Ljava/lang/StringBuilder;

    .line 17
    .line 18
    invoke-direct {p2}, Ljava/lang/StringBuilder;-><init>()V

    .line 19
    .line 20
    .line 21
    const-string p3, "Enter animation not complete, try preload url. Result: "

    .line 22
    .line 23
    invoke-virtual {p2, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 24
    .line 25
    .line 26
    invoke-virtual {p2, p1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    .line 27
    .line 28
    .line 29
    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 30
    .line 31
    .line 32
    move-result-object p1

    .line 33
    const-string p2, "SplashScreenStrategy"

    .line 34
    .line 35
    invoke-static {p2, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 36
    .line 37
    .line 38
    return-void
.end method

.method private k()V
    .locals 3

    .line 1
    iget-object v0, p0, LL/c;->a:Landroid/app/Activity;

    .line 2
    .line 3
    iget v1, p0, LL/c;->b:I

    .line 4
    .line 5
    invoke-static {v0, v1}, LK/L;->b(Landroid/content/Context;I)Landroid/graphics/Bitmap;

    .line 6
    .line 7
    .line 8
    move-result-object v0

    .line 9
    iput-object v0, p0, LL/c;->h:Landroid/graphics/Bitmap;

    .line 10
    .line 11
    if-nez v0, :cond_0

    .line 12
    .line 13
    const-string v0, "SplashScreenStrategy"

    .line 14
    .line 15
    const-string v1, "Failed to retrieve splash image from provided drawable id"

    .line 16
    .line 17
    invoke-static {v0, v1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 18
    .line 19
    .line 20
    return-void

    .line 21
    :cond_0
    new-instance v0, Landroid/widget/ImageView;

    .line 22
    .line 23
    iget-object v1, p0, LL/c;->a:Landroid/app/Activity;

    .line 24
    .line 25
    invoke-direct {v0, v1}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;)V

    .line 26
    .line 27
    .line 28
    new-instance v1, Landroid/view/ViewGroup$LayoutParams;

    .line 29
    .line 30
    const/4 v2, -0x1

    .line 31
    invoke-direct {v1, v2, v2}, Landroid/view/ViewGroup$LayoutParams;-><init>(II)V

    .line 32
    .line 33
    .line 34
    invoke-virtual {v0, v1}, Landroid/view/View;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 35
    .line 36
    .line 37
    iget-object v1, p0, LL/c;->h:Landroid/graphics/Bitmap;

    .line 38
    .line 39
    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setImageBitmap(Landroid/graphics/Bitmap;)V

    .line 40
    .line 41
    .line 42
    iget v1, p0, LL/c;->c:I

    .line 43
    .line 44
    invoke-virtual {v0, v1}, Landroid/view/View;->setBackgroundColor(I)V

    .line 45
    .line 46
    .line 47
    iget-object v1, p0, LL/c;->d:Landroid/widget/ImageView$ScaleType;

    .line 48
    .line 49
    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setScaleType(Landroid/widget/ImageView$ScaleType;)V

    .line 50
    .line 51
    .line 52
    iget-object v1, p0, LL/c;->d:Landroid/widget/ImageView$ScaleType;

    .line 53
    .line 54
    sget-object v2, Landroid/widget/ImageView$ScaleType;->MATRIX:Landroid/widget/ImageView$ScaleType;

    .line 55
    .line 56
    if-ne v1, v2, :cond_1

    .line 57
    .line 58
    iget-object v1, p0, LL/c;->e:Landroid/graphics/Matrix;

    .line 59
    .line 60
    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setImageMatrix(Landroid/graphics/Matrix;)V

    .line 61
    .line 62
    .line 63
    :cond_1
    iget-object v1, p0, LL/c;->a:Landroid/app/Activity;

    .line 64
    .line 65
    invoke-virtual {v1, v0}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V

    .line 66
    .line 67
    .line 68
    return-void
.end method


# virtual methods
.method public a(Ljava/lang/String;Lo/q;)V
    .locals 2

    .line 1
    iput-object p1, p0, LL/c;->j:Ljava/lang/String;

    .line 2
    .line 3
    iget-object v0, p0, LL/c;->a:Landroid/app/Activity;

    .line 4
    .line 5
    const-string v1, "androidx.browser.trusted.category.TrustedWebActivitySplashScreensV1"

    .line 6
    .line 7
    invoke-static {v0, p1, v1}, Ln/g;->a(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;)Z

    .line 8
    .line 9
    .line 10
    move-result v0

    .line 11
    iput-boolean v0, p0, LL/c;->k:Z

    .line 12
    .line 13
    if-nez v0, :cond_0

    .line 14
    .line 15
    new-instance p2, Ljava/lang/StringBuilder;

    .line 16
    .line 17
    invoke-direct {p2}, Ljava/lang/StringBuilder;-><init>()V

    .line 18
    .line 19
    .line 20
    const-string v0, "Provider "

    .line 21
    .line 22
    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 23
    .line 24
    .line 25
    invoke-virtual {p2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 26
    .line 27
    .line 28
    const-string p1, " doesn\'t support splash screens"

    .line 29
    .line 30
    invoke-virtual {p2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 31
    .line 32
    .line 33
    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 34
    .line 35
    .line 36
    move-result-object p1

    .line 37
    const-string p2, "SplashScreenStrategy"

    .line 38
    .line 39
    invoke-static {p2, p1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 40
    .line 41
    .line 42
    return-void

    .line 43
    :cond_0
    invoke-direct {p0}, LL/c;->k()V

    .line 44
    .line 45
    .line 46
    iget-object v0, p0, LL/c;->h:Landroid/graphics/Bitmap;

    .line 47
    .line 48
    if-eqz v0, :cond_1

    .line 49
    .line 50
    invoke-direct {p0, p1, p2}, LL/c;->e(Ljava/lang/String;Lo/q;)V

    .line 51
    .line 52
    .line 53
    :cond_1
    return-void
.end method

.method public b(Lo/q;Ln/f;Ljava/lang/Runnable;)V
    .locals 6

    .line 1
    iget-boolean v0, p0, LL/c;->k:Z

    .line 2
    .line 3
    if-eqz v0, :cond_2

    .line 4
    .line 5
    iget-object v0, p0, LL/c;->h:Landroid/graphics/Bitmap;

    .line 6
    .line 7
    if-nez v0, :cond_0

    .line 8
    .line 9
    goto :goto_0

    .line 10
    :cond_0
    iget-object v0, p0, LL/c;->f:Ljava/lang/String;

    .line 11
    .line 12
    invoke-static {v0}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z

    .line 13
    .line 14
    .line 15
    move-result v0

    .line 16
    if-eqz v0, :cond_1

    .line 17
    .line 18
    const-string p1, "SplashScreenStrategy"

    .line 19
    .line 20
    const-string p2, "FileProvider authority not specified, can\'t transfer splash image."

    .line 21
    .line 22
    invoke-static {p1, p2}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 23
    .line 24
    .line 25
    invoke-interface {p3}, Ljava/lang/Runnable;->run()V

    .line 26
    .line 27
    .line 28
    return-void

    .line 29
    :cond_1
    new-instance v0, LL/d;

    .line 30
    .line 31
    iget-object v1, p0, LL/c;->a:Landroid/app/Activity;

    .line 32
    .line 33
    iget-object v2, p0, LL/c;->h:Landroid/graphics/Bitmap;

    .line 34
    .line 35
    iget-object v3, p0, LL/c;->f:Ljava/lang/String;

    .line 36
    .line 37
    iget-object v5, p0, LL/c;->j:Ljava/lang/String;

    .line 38
    .line 39
    move-object v4, p2

    .line 40
    invoke-direct/range {v0 .. v5}, LL/d;-><init>(Landroid/content/Context;Landroid/graphics/Bitmap;Ljava/lang/String;Ln/f;Ljava/lang/String;)V

    .line 41
    .line 42
    .line 43
    iput-object v0, p0, LL/c;->i:LL/d;

    .line 44
    .line 45
    new-instance p2, LL/a;

    .line 46
    .line 47
    invoke-direct {p2, p0, p1, p3, v4}, LL/a;-><init>(LL/c;Lo/q;Ljava/lang/Runnable;Ln/f;)V

    .line 48
    .line 49
    .line 50
    invoke-virtual {v0, p2}, LL/d;->h(LL/d$b;)V

    .line 51
    .line 52
    .line 53
    return-void

    .line 54
    :cond_2
    :goto_0
    invoke-interface {p3}, Ljava/lang/Runnable;->run()V

    .line 55
    .line 56
    .line 57
    return-void
.end method

.method public f()V
    .locals 1

    .line 1
    iget-object v0, p0, LL/c;->i:LL/d;

    .line 2
    .line 3
    if-eqz v0, :cond_0

    .line 4
    .line 5
    invoke-virtual {v0}, LL/d;->g()V

    .line 6
    .line 7
    .line 8
    :cond_0
    return-void
.end method

.method public h()V
    .locals 1

    .line 1
    const/4 v0, 0x1

    .line 2
    iput-boolean v0, p0, LL/c;->l:Z

    .line 3
    .line 4
    iget-object v0, p0, LL/c;->m:Ljava/lang/Runnable;

    .line 5
    .line 6
    if-eqz v0, :cond_0

    .line 7
    .line 8
    invoke-interface {v0}, Ljava/lang/Runnable;->run()V

    .line 9
    .line 10
    .line 11
    const/4 v0, 0x0

    .line 12
    iput-object v0, p0, LL/c;->m:Ljava/lang/Runnable;

    .line 13
    .line 14
    :cond_0
    return-void
.end method
