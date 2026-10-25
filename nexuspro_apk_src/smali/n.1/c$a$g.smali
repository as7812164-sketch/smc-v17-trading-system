.class Ln/c$a$g;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Ln/c$a;->h(IILandroid/os/Bundle;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic a:I

.field final synthetic b:I

.field final synthetic c:Landroid/os/Bundle;

.field final synthetic d:Ln/c$a;


# direct methods
.method constructor <init>(Ln/c$a;IILandroid/os/Bundle;)V
    .locals 0

    .line 1
    iput-object p1, p0, Ln/c$a$g;->d:Ln/c$a;

    .line 2
    .line 3
    iput p2, p0, Ln/c$a$g;->a:I

    .line 4
    .line 5
    iput p3, p0, Ln/c$a$g;->b:I

    .line 6
    .line 7
    iput-object p4, p0, Ln/c$a$g;->c:Landroid/os/Bundle;

    .line 8
    .line 9
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 10
    .line 11
    .line 12
    return-void
.end method


# virtual methods
.method public run()V
    .locals 4

    .line 1
    iget-object v0, p0, Ln/c$a$g;->d:Ln/c$a;

    .line 2
    .line 3
    iget-object v0, v0, Ln/c$a;->f:Ln/b;

    .line 4
    .line 5
    iget v1, p0, Ln/c$a$g;->a:I

    .line 6
    .line 7
    iget v2, p0, Ln/c$a$g;->b:I

    .line 8
    .line 9
    iget-object v3, p0, Ln/c$a$g;->c:Landroid/os/Bundle;

    .line 10
    .line 11
    invoke-virtual {v0, v1, v2, v3}, Ln/b;->d(IILandroid/os/Bundle;)V

    .line 12
    .line 13
    .line 14
    return-void
.end method
