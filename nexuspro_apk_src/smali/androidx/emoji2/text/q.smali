.class public final Landroidx/emoji2/text/q;
.super Landroidx/emoji2/text/j;
.source "SourceFile"


# static fields
.field private static g:Landroid/graphics/Paint;


# instance fields
.field private f:Landroid/text/TextPaint;


# direct methods
.method public constructor <init>(Landroidx/emoji2/text/p;)V
    .locals 0

    .line 1
    invoke-direct {p0, p1}, Landroidx/emoji2/text/j;-><init>(Landroidx/emoji2/text/p;)V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method private c(Ljava/lang/CharSequence;IILandroid/graphics/Paint;)Landroid/text/TextPaint;
    .locals 2

    .line 1
    instance-of v0, p1, Landroid/text/Spanned;

    .line 2
    .line 3
    const/4 v1, 0x0

    .line 4
    if-eqz v0, :cond_5

    .line 5
    .line 6
    check-cast p1, Landroid/text/Spanned;

    .line 7
    .line 8
    const-class v0, Landroid/text/style/CharacterStyle;

    .line 9
    .line 10
    invoke-interface {p1, p2, p3, v0}, Landroid/text/Spanned;->getSpans(IILjava/lang/Class;)[Ljava/lang/Object;

    .line 11
    .line 12
    .line 13
    move-result-object p1

    .line 14
    check-cast p1, [Landroid/text/style/CharacterStyle;

    .line 15
    .line 16
    array-length p2, p1

    .line 17
    if-eqz p2, :cond_3

    .line 18
    .line 19
    array-length p2, p1

    .line 20
    const/4 p3, 0x0

    .line 21
    const/4 v0, 0x1

    .line 22
    if-ne p2, v0, :cond_0

    .line 23
    .line 24
    aget-object p2, p1, p3

    .line 25
    .line 26
    if-ne p2, p0, :cond_0

    .line 27
    .line 28
    goto :goto_1

    .line 29
    :cond_0
    iget-object p2, p0, Landroidx/emoji2/text/q;->f:Landroid/text/TextPaint;

    .line 30
    .line 31
    if-nez p2, :cond_1

    .line 32
    .line 33
    new-instance p2, Landroid/text/TextPaint;

    .line 34
    .line 35
    invoke-direct {p2}, Landroid/text/TextPaint;-><init>()V

    .line 36
    .line 37
    .line 38
    iput-object p2, p0, Landroidx/emoji2/text/q;->f:Landroid/text/TextPaint;

    .line 39
    .line 40
    :cond_1
    invoke-virtual {p2, p4}, Landroid/graphics/Paint;->set(Landroid/graphics/Paint;)V

    .line 41
    .line 42
    .line 43
    :goto_0
    array-length p4, p1

    .line 44
    if-ge p3, p4, :cond_2

    .line 45
    .line 46
    aget-object p4, p1, p3

    .line 47
    .line 48
    invoke-virtual {p4, p2}, Landroid/text/style/CharacterStyle;->updateDrawState(Landroid/text/TextPaint;)V

    .line 49
    .line 50
    .line 51
    add-int/lit8 p3, p3, 0x1

    .line 52
    .line 53
    goto :goto_0

    .line 54
    :cond_2
    return-object p2

    .line 55
    :cond_3
    :goto_1
    instance-of p1, p4, Landroid/text/TextPaint;

    .line 56
    .line 57
    if-eqz p1, :cond_4

    .line 58
    .line 59
    check-cast p4, Landroid/text/TextPaint;

    .line 60
    .line 61
    return-object p4

    .line 62
    :cond_4
    return-object v1

    .line 63
    :cond_5
    instance-of p1, p4, Landroid/text/TextPaint;

    .line 64
    .line 65
    if-eqz p1, :cond_6

    .line 66
    .line 67
    check-cast p4, Landroid/text/TextPaint;

    .line 68
    .line 69
    return-object p4

    .line 70
    :cond_6
    return-object v1
.end method

.method private static e()Landroid/graphics/Paint;
    .locals 2

    .line 1
    sget-object v0, Landroidx/emoji2/text/q;->g:Landroid/graphics/Paint;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    new-instance v0, Landroid/text/TextPaint;

    .line 6
    .line 7
    invoke-direct {v0}, Landroid/text/TextPaint;-><init>()V

    .line 8
    .line 9
    .line 10
    sput-object v0, Landroidx/emoji2/text/q;->g:Landroid/graphics/Paint;

    .line 11
    .line 12
    invoke-static {}, Landroidx/emoji2/text/f;->c()Landroidx/emoji2/text/f;

    .line 13
    .line 14
    .line 15
    move-result-object v1

    .line 16
    invoke-virtual {v1}, Landroidx/emoji2/text/f;->d()I

    .line 17
    .line 18
    .line 19
    move-result v1

    .line 20
    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 21
    .line 22
    .line 23
    sget-object v0, Landroidx/emoji2/text/q;->g:Landroid/graphics/Paint;

    .line 24
    .line 25
    sget-object v1, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    .line 26
    .line 27
    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 28
    .line 29
    .line 30
    :cond_0
    sget-object v0, Landroidx/emoji2/text/q;->g:Landroid/graphics/Paint;

    .line 31
    .line 32
    return-object v0
.end method


# virtual methods
.method d(Landroid/graphics/Canvas;Landroid/text/TextPaint;FFFF)V
    .locals 4

    .line 1
    invoke-virtual {p2}, Landroid/graphics/Paint;->getColor()I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    invoke-virtual {p2}, Landroid/graphics/Paint;->getStyle()Landroid/graphics/Paint$Style;

    .line 6
    .line 7
    .line 8
    move-result-object v1

    .line 9
    iget v2, p2, Landroid/text/TextPaint;->bgColor:I

    .line 10
    .line 11
    invoke-virtual {p2, v2}, Landroid/graphics/Paint;->setColor(I)V

    .line 12
    .line 13
    .line 14
    sget-object v2, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    .line 15
    .line 16
    invoke-virtual {p2, v2}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 17
    .line 18
    .line 19
    move v3, p6

    .line 20
    move-object p6, p2

    .line 21
    move p2, p3

    .line 22
    move p3, p5

    .line 23
    move p5, v3

    .line 24
    invoke-virtual/range {p1 .. p6}, Landroid/graphics/Canvas;->drawRect(FFFFLandroid/graphics/Paint;)V

    .line 25
    .line 26
    .line 27
    invoke-virtual {p6, v1}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 28
    .line 29
    .line 30
    invoke-virtual {p6, v0}, Landroid/graphics/Paint;->setColor(I)V

    .line 31
    .line 32
    .line 33
    return-void
.end method

.method public draw(Landroid/graphics/Canvas;Ljava/lang/CharSequence;IIFIIILandroid/graphics/Paint;)V
    .locals 10

    move/from16 v0, p6

    move/from16 v1, p8

    move-object/from16 v2, p9

    .line 1
    invoke-direct {p0, p2, p3, p4, v2}, Landroidx/emoji2/text/q;->c(Ljava/lang/CharSequence;IILandroid/graphics/Paint;)Landroid/text/TextPaint;

    move-result-object v5

    if-eqz v5, :cond_0

    .line 2
    iget p2, v5, Landroid/text/TextPaint;->bgColor:I

    if-eqz p2, :cond_0

    .line 3
    invoke-virtual {p0}, Landroidx/emoji2/text/j;->b()I

    move-result p2

    int-to-float p2, p2

    add-float v7, p5, p2

    int-to-float v8, v0

    int-to-float v9, v1

    move-object v3, p0

    move-object v4, p1

    move v6, p5

    invoke-virtual/range {v3 .. v9}, Landroidx/emoji2/text/q;->d(Landroid/graphics/Canvas;Landroid/text/TextPaint;FFFF)V

    :cond_0
    move-object p2, v5

    .line 4
    invoke-static {}, Landroidx/emoji2/text/f;->c()Landroidx/emoji2/text/f;

    move-result-object p3

    invoke-virtual {p3}, Landroidx/emoji2/text/f;->j()Z

    move-result p3

    if-eqz p3, :cond_1

    int-to-float v5, v0

    .line 5
    invoke-virtual {p0}, Landroidx/emoji2/text/j;->b()I

    move-result p3

    int-to-float p3, p3

    add-float v6, p5, p3

    int-to-float v7, v1

    invoke-static {}, Landroidx/emoji2/text/q;->e()Landroid/graphics/Paint;

    move-result-object v8

    move-object v3, p1

    move v4, p5

    invoke-virtual/range {v3 .. v8}, Landroid/graphics/Canvas;->drawRect(FFFFLandroid/graphics/Paint;)V

    .line 6
    :cond_1
    invoke-virtual {p0}, Landroidx/emoji2/text/j;->a()Landroidx/emoji2/text/p;

    move-result-object p3

    move/from16 p4, p7

    int-to-float p4, p4

    if-eqz p2, :cond_2

    goto :goto_0

    :cond_2
    move-object p2, v2

    :goto_0
    invoke-virtual {p3, p1, p5, p4, p2}, Landroidx/emoji2/text/p;->a(Landroid/graphics/Canvas;FFLandroid/graphics/Paint;)V

    return-void
.end method
