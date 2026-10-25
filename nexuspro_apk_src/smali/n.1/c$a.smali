.class Ln/c$a;
.super La/a$a;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Ln/c;->c(Ln/b;)La/a$a;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field private e:Landroid/os/Handler;

.field final synthetic f:Ln/b;

.field final synthetic g:Ln/c;


# direct methods
.method constructor <init>(Ln/c;Ln/b;)V
    .locals 0

    .line 1
    iput-object p1, p0, Ln/c$a;->g:Ln/c;

    .line 2
    .line 3
    iput-object p2, p0, Ln/c$a;->f:Ln/b;

    .line 4
    .line 5
    invoke-direct {p0}, La/a$a;-><init>()V

    .line 6
    .line 7
    .line 8
    new-instance p1, Landroid/os/Handler;

    .line 9
    .line 10
    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    .line 11
    .line 12
    .line 13
    move-result-object p2

    .line 14
    invoke-direct {p1, p2}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    .line 15
    .line 16
    .line 17
    iput-object p1, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 18
    .line 19
    return-void
.end method


# virtual methods
.method public a(Ljava/lang/String;Landroid/os/Bundle;)V
    .locals 2

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$e;

    .line 9
    .line 10
    invoke-direct {v1, p0, p1, p2}, Ln/c$a$e;-><init>(Ln/c$a;Ljava/lang/String;Landroid/os/Bundle;)V

    .line 11
    .line 12
    .line 13
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 14
    .line 15
    .line 16
    return-void
.end method

.method public d(Ljava/lang/String;Landroid/os/Bundle;)V
    .locals 2

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$c;

    .line 9
    .line 10
    invoke-direct {v1, p0, p1, p2}, Ln/c$a$c;-><init>(Ln/c$a;Ljava/lang/String;Landroid/os/Bundle;)V

    .line 11
    .line 12
    .line 13
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 14
    .line 15
    .line 16
    return-void
.end method

.method public f(IIIIILandroid/os/Bundle;)V
    .locals 9

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$i;

    .line 9
    .line 10
    move-object v2, p0

    .line 11
    move v3, p1

    .line 12
    move v4, p2

    .line 13
    move v5, p3

    .line 14
    move v6, p4

    .line 15
    move v7, p5

    .line 16
    move-object v8, p6

    .line 17
    invoke-direct/range {v1 .. v8}, Ln/c$a$i;-><init>(Ln/c$a;IIIIILandroid/os/Bundle;)V

    .line 18
    .line 19
    .line 20
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 21
    .line 22
    .line 23
    return-void
.end method

.method public g(Landroid/os/Bundle;)V
    .locals 2

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$d;

    .line 9
    .line 10
    invoke-direct {v1, p0, p1}, Ln/c$a$d;-><init>(Ln/c$a;Landroid/os/Bundle;)V

    .line 11
    .line 12
    .line 13
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 14
    .line 15
    .line 16
    return-void
.end method

.method public h(IILandroid/os/Bundle;)V
    .locals 2

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$g;

    .line 9
    .line 10
    invoke-direct {v1, p0, p1, p2, p3}, Ln/c$a$g;-><init>(Ln/c$a;IILandroid/os/Bundle;)V

    .line 11
    .line 12
    .line 13
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 14
    .line 15
    .line 16
    return-void
.end method

.method public l(Ljava/lang/String;Landroid/os/Bundle;)Landroid/os/Bundle;
    .locals 1

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    const/4 p1, 0x0

    .line 6
    return-object p1

    .line 7
    :cond_0
    invoke-virtual {v0, p1, p2}, Ln/b;->b(Ljava/lang/String;Landroid/os/Bundle;)Landroid/os/Bundle;

    .line 8
    .line 9
    .line 10
    move-result-object p1

    .line 11
    return-object p1
.end method

.method public o(ILandroid/net/Uri;ZLandroid/os/Bundle;)V
    .locals 7

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$f;

    .line 9
    .line 10
    move-object v2, p0

    .line 11
    move v3, p1

    .line 12
    move-object v4, p2

    .line 13
    move v5, p3

    .line 14
    move-object v6, p4

    .line 15
    invoke-direct/range {v1 .. v6}, Ln/c$a$f;-><init>(Ln/c$a;ILandroid/net/Uri;ZLandroid/os/Bundle;)V

    .line 16
    .line 17
    .line 18
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 19
    .line 20
    .line 21
    return-void
.end method

.method public r(Landroid/os/Bundle;)V
    .locals 2

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$h;

    .line 9
    .line 10
    invoke-direct {v1, p0, p1}, Ln/c$a$h;-><init>(Ln/c$a;Landroid/os/Bundle;)V

    .line 11
    .line 12
    .line 13
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 14
    .line 15
    .line 16
    return-void
.end method

.method public s(Landroid/os/Bundle;)V
    .locals 2

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$j;

    .line 9
    .line 10
    invoke-direct {v1, p0, p1}, Ln/c$a$j;-><init>(Ln/c$a;Landroid/os/Bundle;)V

    .line 11
    .line 12
    .line 13
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 14
    .line 15
    .line 16
    return-void
.end method

.method public v(Landroid/os/Bundle;)V
    .locals 2

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$a;

    .line 9
    .line 10
    invoke-direct {v1, p0, p1}, Ln/c$a$a;-><init>(Ln/c$a;Landroid/os/Bundle;)V

    .line 11
    .line 12
    .line 13
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 14
    .line 15
    .line 16
    return-void
.end method

.method public w(ILandroid/os/Bundle;)V
    .locals 2

    .line 1
    iget-object v0, p0, Ln/c$a;->f:Ln/b;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, Ln/c$a;->e:Landroid/os/Handler;

    .line 7
    .line 8
    new-instance v1, Ln/c$a$b;

    .line 9
    .line 10
    invoke-direct {v1, p0, p1, p2}, Ln/c$a$b;-><init>(Ln/c$a;ILandroid/os/Bundle;)V

    .line 11
    .line 12
    .line 13
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 14
    .line 15
    .line 16
    return-void
.end method
