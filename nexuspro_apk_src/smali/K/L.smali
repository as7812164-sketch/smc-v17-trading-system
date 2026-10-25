.class public abstract LK/L;
.super Ljava/lang/Object;
.source "SourceFile"


# direct methods
.method private static a(Landroid/app/Activity;I)V
    .locals 1

    .line 1
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    .line 2
    .line 3
    .line 4
    move-result-object p0

    .line 5
    invoke-virtual {p0}, Landroid/view/Window;->getDecorView()Landroid/view/View;

    .line 6
    .line 7
    .line 8
    move-result-object p0

    .line 9
    invoke-virtual {p0}, Landroid/view/View;->getRootView()Landroid/view/View;

    .line 10
    .line 11
    .line 12
    move-result-object p0

    .line 13
    invoke-virtual {p0}, Landroid/view/View;->getSystemUiVisibility()I

    .line 14
    .line 15
    .line 16
    move-result v0

    .line 17
    or-int/2addr p1, v0

    .line 18
    invoke-virtual {p0, p1}, Landroid/view/View;->setSystemUiVisibility(I)V

    .line 19
    .line 20
    .line 21
    return-void
.end method

.method public static b(Landroid/content/Context;I)Landroid/graphics/Bitmap;
    .locals 4

    .line 1
    invoke-static {p0, p1}, Landroidx/core/content/a;->c(Landroid/content/Context;I)Landroid/graphics/drawable/Drawable;

    .line 2
    .line 3
    .line 4
    move-result-object p0

    .line 5
    if-nez p0, :cond_0

    .line 6
    .line 7
    const/4 p0, 0x0

    .line 8
    return-object p0

    .line 9
    :cond_0
    invoke-static {p0}, Landroidx/core/graphics/drawable/a;->h(Landroid/graphics/drawable/Drawable;)Landroid/graphics/drawable/Drawable;

    .line 10
    .line 11
    .line 12
    move-result-object p0

    .line 13
    invoke-virtual {p0}, Landroid/graphics/drawable/Drawable;->getIntrinsicWidth()I

    .line 14
    .line 15
    .line 16
    move-result p1

    .line 17
    invoke-virtual {p0}, Landroid/graphics/drawable/Drawable;->getIntrinsicHeight()I

    .line 18
    .line 19
    .line 20
    move-result v0

    .line 21
    sget-object v1, Landroid/graphics/Bitmap$Config;->ARGB_8888:Landroid/graphics/Bitmap$Config;

    .line 22
    .line 23
    invoke-static {p1, v0, v1}, Landroid/graphics/Bitmap;->createBitmap(IILandroid/graphics/Bitmap$Config;)Landroid/graphics/Bitmap;

    .line 24
    .line 25
    .line 26
    move-result-object p1

    .line 27
    new-instance v0, Landroid/graphics/Canvas;

    .line 28
    .line 29
    invoke-direct {v0, p1}, Landroid/graphics/Canvas;-><init>(Landroid/graphics/Bitmap;)V

    .line 30
    .line 31
    .line 32
    invoke-virtual {v0}, Landroid/graphics/Canvas;->getWidth()I

    .line 33
    .line 34
    .line 35
    move-result v1

    .line 36
    invoke-virtual {v0}, Landroid/graphics/Canvas;->getHeight()I

    .line 37
    .line 38
    .line 39
    move-result v2

    .line 40
    const/4 v3, 0x0

    .line 41
    invoke-virtual {p0, v3, v3, v1, v2}, Landroid/graphics/drawable/Drawable;->setBounds(IIII)V

    .line 42
    .line 43
    .line 44
    invoke-virtual {p0, v0}, Landroid/graphics/drawable/Drawable;->draw(Landroid/graphics/Canvas;)V

    .line 45
    .line 46
    .line 47
    return-object p1
.end method

.method private static c(F)F
    .locals 4

    .line 1
    const/high16 v0, 0x437f0000    # 255.0f

    .line 2
    .line 3
    div-float/2addr p0, v0

    .line 4
    const v0, 0x3d20e411    # 0.03928f

    .line 5
    .line 6
    .line 7
    cmpg-float v0, p0, v0

    .line 8
    .line 9
    if-gez v0, :cond_0

    .line 10
    .line 11
    const v0, 0x414eb852    # 12.92f

    .line 12
    .line 13
    .line 14
    div-float/2addr p0, v0

    .line 15
    return p0

    .line 16
    :cond_0
    const v0, 0x3d6147ae    # 0.055f

    .line 17
    .line 18
    .line 19
    add-float/2addr p0, v0

    .line 20
    const v0, 0x3f870a3d    # 1.055f

    .line 21
    .line 22
    .line 23
    div-float/2addr p0, v0

    .line 24
    float-to-double v0, p0

    .line 25
    const-wide v2, 0x4003333340000000L    # 2.4000000953674316

    .line 26
    .line 27
    .line 28
    .line 29
    .line 30
    invoke-static {v0, v1, v2, v3}, Ljava/lang/Math;->pow(DD)D

    .line 31
    .line 32
    .line 33
    move-result-wide v0

    .line 34
    double-to-float p0, v0

    .line 35
    return p0
.end method

.method public static d(Landroid/app/Activity;I)V
    .locals 2

    .line 1
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 2
    .line 3
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    .line 4
    .line 5
    .line 6
    move-result-object v1

    .line 7
    invoke-virtual {v1, p1}, Landroid/view/Window;->setNavigationBarColor(I)V

    .line 8
    .line 9
    .line 10
    const/16 v1, 0x1a

    .line 11
    .line 12
    if-lt v0, v1, :cond_0

    .line 13
    .line 14
    invoke-static {p1}, LK/L;->f(I)Z

    .line 15
    .line 16
    .line 17
    move-result p1

    .line 18
    if-eqz p1, :cond_0

    .line 19
    .line 20
    const/16 p1, 0x10

    .line 21
    .line 22
    invoke-static {p0, p1}, LK/L;->a(Landroid/app/Activity;I)V

    .line 23
    .line 24
    .line 25
    :cond_0
    return-void
.end method

.method public static e(Landroid/app/Activity;I)V
    .locals 1

    .line 1
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    invoke-virtual {v0, p1}, Landroid/view/Window;->setStatusBarColor(I)V

    .line 6
    .line 7
    .line 8
    invoke-static {p1}, LK/L;->f(I)Z

    .line 9
    .line 10
    .line 11
    move-result p1

    .line 12
    if-eqz p1, :cond_0

    .line 13
    .line 14
    const/16 p1, 0x2000

    .line 15
    .line 16
    invoke-static {p0, p1}, LK/L;->a(Landroid/app/Activity;I)V

    .line 17
    .line 18
    .line 19
    :cond_0
    return-void
.end method

.method private static f(I)Z
    .locals 3

    .line 1
    invoke-static {p0}, Landroid/graphics/Color;->red(I)I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    int-to-float v0, v0

    .line 6
    invoke-static {v0}, LK/L;->c(F)F

    .line 7
    .line 8
    .line 9
    move-result v0

    .line 10
    const v1, 0x3e59b3d0    # 0.2126f

    .line 11
    .line 12
    .line 13
    mul-float/2addr v0, v1

    .line 14
    invoke-static {p0}, Landroid/graphics/Color;->green(I)I

    .line 15
    .line 16
    .line 17
    move-result v1

    .line 18
    int-to-float v1, v1

    .line 19
    invoke-static {v1}, LK/L;->c(F)F

    .line 20
    .line 21
    .line 22
    move-result v1

    .line 23
    const v2, 0x3f371759    # 0.7152f

    .line 24
    .line 25
    .line 26
    mul-float/2addr v1, v2

    .line 27
    add-float/2addr v0, v1

    .line 28
    invoke-static {p0}, Landroid/graphics/Color;->blue(I)I

    .line 29
    .line 30
    .line 31
    move-result p0

    .line 32
    int-to-float p0, p0

    .line 33
    invoke-static {p0}, LK/L;->c(F)F

    .line 34
    .line 35
    .line 36
    move-result p0

    .line 37
    const v1, 0x3d93dd98    # 0.0722f

    .line 38
    .line 39
    .line 40
    mul-float/2addr p0, v1

    .line 41
    add-float/2addr v0, p0

    .line 42
    const p0, 0x3d4ccccd    # 0.05f

    .line 43
    .line 44
    .line 45
    add-float/2addr v0, p0

    .line 46
    const p0, 0x3f866666    # 1.05f

    .line 47
    .line 48
    .line 49
    div-float/2addr p0, v0

    .line 50
    invoke-static {p0}, Ljava/lang/Math;->abs(F)F

    .line 51
    .line 52
    .line 53
    move-result p0

    .line 54
    const/high16 v0, 0x40400000    # 3.0f

    .line 55
    .line 56
    cmpg-float p0, p0, v0

    .line 57
    .line 58
    if-gez p0, :cond_0

    .line 59
    .line 60
    const/4 p0, 0x1

    .line 61
    return p0

    .line 62
    :cond_0
    const/4 p0, 0x0

    .line 63
    return p0
.end method
