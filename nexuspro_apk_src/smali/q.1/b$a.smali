.class final Lq/b$a;
.super Lq/e;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lq/b;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x12
    name = "a"
.end annotation


# instance fields
.field final synthetic d:Lq/b;


# direct methods
.method public constructor <init>(Lq/b;)V
    .locals 0

    .line 1
    iput-object p1, p0, Lq/b$a;->d:Lq/b;

    .line 2
    .line 3
    invoke-virtual {p1}, Lq/b;->e()I

    .line 4
    .line 5
    .line 6
    move-result p1

    .line 7
    invoke-direct {p0, p1}, Lq/e;-><init>(I)V

    .line 8
    .line 9
    .line 10
    return-void
.end method


# virtual methods
.method protected a(I)Ljava/lang/Object;
    .locals 1

    .line 1
    iget-object v0, p0, Lq/b$a;->d:Lq/b;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Lq/b;->j(I)Ljava/lang/Object;

    .line 4
    .line 5
    .line 6
    move-result-object p1

    .line 7
    return-object p1
.end method

.method protected b(I)V
    .locals 1

    .line 1
    iget-object v0, p0, Lq/b$a;->d:Lq/b;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Lq/b;->f(I)Ljava/lang/Object;

    .line 4
    .line 5
    .line 6
    return-void
.end method
