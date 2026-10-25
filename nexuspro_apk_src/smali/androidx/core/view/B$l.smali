.class Landroidx/core/view/B$l;
.super Ljava/lang/Object;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Landroidx/core/view/B;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0xa
    name = "l"
.end annotation


# static fields
.field static final b:Landroidx/core/view/B;


# instance fields
.field final a:Landroidx/core/view/B;


# direct methods
.method static constructor <clinit>()V
    .locals 1

    .line 1
    new-instance v0, Landroidx/core/view/B$b;

    .line 2
    .line 3
    invoke-direct {v0}, Landroidx/core/view/B$b;-><init>()V

    .line 4
    .line 5
    .line 6
    invoke-virtual {v0}, Landroidx/core/view/B$b;->a()Landroidx/core/view/B;

    .line 7
    .line 8
    .line 9
    move-result-object v0

    .line 10
    invoke-virtual {v0}, Landroidx/core/view/B;->a()Landroidx/core/view/B;

    .line 11
    .line 12
    .line 13
    move-result-object v0

    .line 14
    invoke-virtual {v0}, Landroidx/core/view/B;->b()Landroidx/core/view/B;

    .line 15
    .line 16
    .line 17
    move-result-object v0

    .line 18
    invoke-virtual {v0}, Landroidx/core/view/B;->c()Landroidx/core/view/B;

    .line 19
    .line 20
    .line 21
    move-result-object v0

    .line 22
    sput-object v0, Landroidx/core/view/B$l;->b:Landroidx/core/view/B;

    .line 23
    .line 24
    return-void
.end method

.method constructor <init>(Landroidx/core/view/B;)V
    .locals 0

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 2
    .line 3
    .line 4
    iput-object p1, p0, Landroidx/core/view/B$l;->a:Landroidx/core/view/B;

    .line 5
    .line 6
    return-void
.end method


# virtual methods
.method a()Landroidx/core/view/B;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/core/view/B$l;->a:Landroidx/core/view/B;

    .line 2
    .line 3
    return-object v0
.end method

.method b()Landroidx/core/view/B;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/core/view/B$l;->a:Landroidx/core/view/B;

    .line 2
    .line 3
    return-object v0
.end method

.method c()Landroidx/core/view/B;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/core/view/B$l;->a:Landroidx/core/view/B;

    .line 2
    .line 3
    return-object v0
.end method

.method d(Landroid/view/View;)V
    .locals 0

    .line 1
    return-void
.end method

.method e(Landroidx/core/view/B;)V
    .locals 0

    .line 1
    return-void
.end method

.method public equals(Ljava/lang/Object;)Z
    .locals 4

    .line 1
    const/4 v0, 0x1

    .line 2
    if-ne p0, p1, :cond_0

    .line 3
    .line 4
    return v0

    .line 5
    :cond_0
    instance-of v1, p1, Landroidx/core/view/B$l;

    .line 6
    .line 7
    const/4 v2, 0x0

    .line 8
    if-nez v1, :cond_1

    .line 9
    .line 10
    return v2

    .line 11
    :cond_1
    check-cast p1, Landroidx/core/view/B$l;

    .line 12
    .line 13
    invoke-virtual {p0}, Landroidx/core/view/B$l;->o()Z

    .line 14
    .line 15
    .line 16
    move-result v1

    .line 17
    invoke-virtual {p1}, Landroidx/core/view/B$l;->o()Z

    .line 18
    .line 19
    .line 20
    move-result v3

    .line 21
    if-ne v1, v3, :cond_2

    .line 22
    .line 23
    invoke-virtual {p0}, Landroidx/core/view/B$l;->n()Z

    .line 24
    .line 25
    .line 26
    move-result v1

    .line 27
    invoke-virtual {p1}, Landroidx/core/view/B$l;->n()Z

    .line 28
    .line 29
    .line 30
    move-result v3

    .line 31
    if-ne v1, v3, :cond_2

    .line 32
    .line 33
    invoke-virtual {p0}, Landroidx/core/view/B$l;->k()Landroidx/core/graphics/f;

    .line 34
    .line 35
    .line 36
    move-result-object v1

    .line 37
    invoke-virtual {p1}, Landroidx/core/view/B$l;->k()Landroidx/core/graphics/f;

    .line 38
    .line 39
    .line 40
    move-result-object v3

    .line 41
    invoke-static {v1, v3}, Lx/b;->a(Ljava/lang/Object;Ljava/lang/Object;)Z

    .line 42
    .line 43
    .line 44
    move-result v1

    .line 45
    if-eqz v1, :cond_2

    .line 46
    .line 47
    invoke-virtual {p0}, Landroidx/core/view/B$l;->i()Landroidx/core/graphics/f;

    .line 48
    .line 49
    .line 50
    move-result-object v1

    .line 51
    invoke-virtual {p1}, Landroidx/core/view/B$l;->i()Landroidx/core/graphics/f;

    .line 52
    .line 53
    .line 54
    move-result-object v3

    .line 55
    invoke-static {v1, v3}, Lx/b;->a(Ljava/lang/Object;Ljava/lang/Object;)Z

    .line 56
    .line 57
    .line 58
    move-result v1

    .line 59
    if-eqz v1, :cond_2

    .line 60
    .line 61
    invoke-virtual {p0}, Landroidx/core/view/B$l;->f()Landroidx/core/view/h;

    .line 62
    .line 63
    .line 64
    move-result-object v1

    .line 65
    invoke-virtual {p1}, Landroidx/core/view/B$l;->f()Landroidx/core/view/h;

    .line 66
    .line 67
    .line 68
    move-result-object p1

    .line 69
    invoke-static {v1, p1}, Lx/b;->a(Ljava/lang/Object;Ljava/lang/Object;)Z

    .line 70
    .line 71
    .line 72
    move-result p1

    .line 73
    if-eqz p1, :cond_2

    .line 74
    .line 75
    return v0

    .line 76
    :cond_2
    return v2
.end method

.method f()Landroidx/core/view/h;
    .locals 1

    .line 1
    const/4 v0, 0x0

    return-object v0
.end method

.method g(I)Landroidx/core/graphics/f;
    .locals 0

    .line 1
    sget-object p1, Landroidx/core/graphics/f;->e:Landroidx/core/graphics/f;

    .line 2
    .line 3
    return-object p1
.end method

.method h()Landroidx/core/graphics/f;
    .locals 1

    .line 1
    invoke-virtual {p0}, Landroidx/core/view/B$l;->k()Landroidx/core/graphics/f;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    return-object v0
.end method

.method public hashCode()I
    .locals 5

    .line 1
    invoke-virtual {p0}, Landroidx/core/view/B$l;->o()Z

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    invoke-static {v0}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    .line 6
    .line 7
    .line 8
    move-result-object v0

    .line 9
    invoke-virtual {p0}, Landroidx/core/view/B$l;->n()Z

    .line 10
    .line 11
    .line 12
    move-result v1

    .line 13
    invoke-static {v1}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    .line 14
    .line 15
    .line 16
    move-result-object v1

    .line 17
    invoke-virtual {p0}, Landroidx/core/view/B$l;->k()Landroidx/core/graphics/f;

    .line 18
    .line 19
    .line 20
    move-result-object v2

    .line 21
    invoke-virtual {p0}, Landroidx/core/view/B$l;->i()Landroidx/core/graphics/f;

    .line 22
    .line 23
    .line 24
    move-result-object v3

    .line 25
    invoke-virtual {p0}, Landroidx/core/view/B$l;->f()Landroidx/core/view/h;

    .line 26
    .line 27
    .line 28
    move-result-object v4

    .line 29
    filled-new-array {v0, v1, v2, v3, v4}, [Ljava/lang/Object;

    .line 30
    .line 31
    .line 32
    move-result-object v0

    .line 33
    invoke-static {v0}, Lx/b;->b([Ljava/lang/Object;)I

    .line 34
    .line 35
    .line 36
    move-result v0

    .line 37
    return v0
.end method

.method i()Landroidx/core/graphics/f;
    .locals 1

    .line 1
    sget-object v0, Landroidx/core/graphics/f;->e:Landroidx/core/graphics/f;

    .line 2
    .line 3
    return-object v0
.end method

.method j()Landroidx/core/graphics/f;
    .locals 1

    .line 1
    invoke-virtual {p0}, Landroidx/core/view/B$l;->k()Landroidx/core/graphics/f;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    return-object v0
.end method

.method k()Landroidx/core/graphics/f;
    .locals 1

    .line 1
    sget-object v0, Landroidx/core/graphics/f;->e:Landroidx/core/graphics/f;

    .line 2
    .line 3
    return-object v0
.end method

.method l()Landroidx/core/graphics/f;
    .locals 1

    .line 1
    invoke-virtual {p0}, Landroidx/core/view/B$l;->k()Landroidx/core/graphics/f;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    return-object v0
.end method

.method m(IIII)Landroidx/core/view/B;
    .locals 0

    .line 1
    sget-object p1, Landroidx/core/view/B$l;->b:Landroidx/core/view/B;

    .line 2
    .line 3
    return-object p1
.end method

.method n()Z
    .locals 1

    .line 1
    const/4 v0, 0x0

    return v0
.end method

.method o()Z
    .locals 1

    .line 1
    const/4 v0, 0x0

    return v0
.end method

.method public p([Landroidx/core/graphics/f;)V
    .locals 0

    .line 1
    return-void
.end method

.method q(Landroidx/core/graphics/f;)V
    .locals 0

    .line 1
    return-void
.end method

.method r(Landroidx/core/view/B;)V
    .locals 0

    .line 1
    return-void
.end method

.method public s(Landroidx/core/graphics/f;)V
    .locals 0

    .line 1
    return-void
.end method
